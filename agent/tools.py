"""Read-only investigation tools exposed to the agent.

validate_exec() is pure (no docker required) so the allowlist is unit-testable;
execution happens separately and always without a shell.
"""

import shlex

from common import lab
from common.text import truncate

REDIS_SIMPLE = {
    "ping", "info", "llen", "lrange", "dbsize", "scan", "type", "ttl",
    "get", "keys", "exists", "strlen", "hgetall", "lindex", "xlen", "randomkey",
}
REDIS_SUBCOMMANDS = {
    "config": {"get"},
    "client": {"list", "info"},
    "memory": {"usage", "stats", "doctor"},
    "slowlog": {"get"},
    "object": {"encoding", "idletime", "freq"},
}

MAX_LOG_LINES = 500

# Services that can originate a probe (must have a usable exec environment)
# and lab services that listen on a port, with their default ports.
PROBE_SOURCES = ["api", "worker", "nginx", "redis", "postgres"]
PROBE_TARGET_PORTS = {"postgres": 5432, "redis": 6379, "api": 8000, "nginx": 80}
# python:*-slim images probe via the stdlib; alpine-based images via busybox.
PYTHON_SOURCES = {"api", "worker"}

_PROBE_SCRIPT = """\
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
try:
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    addrs = sorted({info[4][0] for info in infos})
    print(f"dns: {host} -> {', '.join(addrs)}")
except OSError as exc:
    print(f"dns: FAILED to resolve {host!r}: {exc}")
    sys.exit(0)
try:
    with socket.create_connection((addrs[0], port), timeout=3):
        print(f"tcp: connect {addrs[0]}:{port} OK")
except OSError as exc:
    print(f"tcp: connect {addrs[0]}:{port} FAILED: {exc}")
"""


def validate_probe(from_service: str, target: str) -> dict:
    """Parse a probe request into a plan, or raise ValueError."""
    if from_service not in PROBE_SOURCES:
        raise ValueError(f"from_service must be one of {PROBE_SOURCES}")
    host, _, port_text = str(target).partition(":")
    if host not in PROBE_TARGET_PORTS:
        raise ValueError(
            f"target must be a lab service {sorted(PROBE_TARGET_PORTS)}, "
            "optionally with ':port'"
        )
    if port_text:
        if not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
            raise ValueError(f"invalid port {port_text!r}")
        port = int(port_text)
    else:
        port = PROBE_TARGET_PORTS[host]
    return {"kind": "probe", "from_service": from_service, "host": host, "port": port}


def _execute_probe(plan: dict) -> str:
    exec_prefix = lab.COMPOSE + ["exec", "-T", plan["from_service"]]
    host, port = plan["host"], str(plan["port"])
    if plan["from_service"] in PYTHON_SOURCES:
        _, out = lab.run(exec_prefix + ["python3", "-c", _PROBE_SCRIPT, host, port])
        return out
    rc, dns_out = lab.run(exec_prefix + ["nslookup", host])
    lines = [f"dns lookup of {host!r} (nslookup, rc={rc}):", dns_out.strip()]
    rc, _ = lab.run(exec_prefix + ["nc", "-z", "-w", "2", host, port])
    lines.append(f"tcp: connect {host}:{port} {'OK' if rc == 0 else f'FAILED (rc={rc})'}")
    return "\n".join(lines)


def probe_connectivity(from_service: str, target: str) -> tuple[str, bool]:
    try:
        plan = validate_probe(from_service, target)
        return truncate(_execute_probe(plan)), False
    except Exception as exc:
        return f"error: {exc}", True


def validate_exec(command: str) -> dict:
    """Parse an exec_readonly command into an execution plan, or raise ValueError."""
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"cannot parse command: {exc}") from exc
    if not tokens:
        raise ValueError("empty command")

    head = tokens[0]
    if head == "redis-cli":
        return _validate_redis(tokens[1:])
    if head == "psql":
        # A single trailing ';' is harmless statement punctuation; strip it.
        command = command.rstrip().rstrip(";")
        # Checked on the raw string so quoting tricks cannot smuggle either
        # character past shlex: ';' separates statements, '\' starts a psql
        # meta-command (e.g. \! runs a shell).
        if ";" in command or "\\" in command:
            raise ValueError("psql: ';' and backslash meta-commands are not allowed")
        parts = command.split(None, 1)
        return _validate_psql(parts[1] if len(parts) > 1 else "")
    if head == "docker":
        return _validate_docker(tokens[1:])
    raise ValueError(
        f"command {head!r} not allowed; use redis-cli, psql, or docker (inspect/stats)"
    )


def _validate_redis(args) -> dict:
    if not args:
        raise ValueError("redis-cli needs a command, e.g. 'redis-cli info memory'")
    if args[0].startswith("-"):
        raise ValueError("redis-cli flags are not allowed; pass a plain command")
    sub = args[0].lower()
    if sub in REDIS_SIMPLE:
        return {"kind": "redis", "args": list(args)}
    if sub in REDIS_SUBCOMMANDS:
        if len(args) < 2 or args[1].lower() not in REDIS_SUBCOMMANDS[sub]:
            allowed = ", ".join(sorted(REDIS_SUBCOMMANDS[sub]))
            raise ValueError(f"redis-cli {sub}: only these subcommands are allowed: {allowed}")
        return {"kind": "redis", "args": list(args)}
    raise ValueError(f"redis-cli command {sub!r} is not in the read-only allowlist")


def _validate_psql(rest: str) -> dict:
    # The SQL is kept raw (not shlex-rejoined) so string literals like
    # 'idle' keep their quotes; it is passed as a single argv element to
    # psql -c, so quoting has no shell meaning here.
    sql = rest.strip()
    if sql.startswith("-c"):
        sql = sql[2:].strip()
    if sql.startswith("-"):
        raise ValueError("psql flags are not allowed; pass 'psql SELECT ...'")
    if len(sql) >= 2 and sql[0] == sql[-1] and sql[0] in "\"'":
        sql = sql[1:-1].strip()  # unwrap one level of -c style outer quoting
    if not sql.lower().startswith("select"):
        raise ValueError("psql: only a single SELECT statement is allowed")
    return {"kind": "psql", "sql": sql}


def _validate_docker(args) -> dict:
    if len(args) == 2 and args[0] == "inspect":
        service = args[1]
        if service not in lab.SERVICES:
            raise ValueError(f"docker inspect: unknown service {service!r} (use one of {lab.SERVICES})")
        return {"kind": "docker_inspect", "service": service}
    stats_args = [a for a in args if a != "--no-stream"]
    if stats_args == ["stats"]:
        return {"kind": "docker_stats", "service": None}
    if len(stats_args) == 2 and stats_args[0] == "stats":
        if stats_args[1] not in lab.SERVICES:
            raise ValueError(f"docker stats: unknown service {stats_args[1]!r}")
        return {"kind": "docker_stats", "service": stats_args[1]}
    raise ValueError("docker: only 'docker inspect <service>' and 'docker stats' are allowed")


def _execute_plan(plan: dict) -> str:
    if plan["kind"] == "redis":
        _, out = lab.run(lab.COMPOSE + ["exec", "-T", "redis", "redis-cli"] + plan["args"])
        return out
    if plan["kind"] == "psql":
        _, out = lab.run(
            lab.COMPOSE + ["exec", "-T", "postgres",
                           "psql", "-U", "readonly", "-d", "shop", "-c", plan["sql"]]
        )
        return out
    if plan["kind"] == "docker_inspect":
        _, out = lab.run(["docker", "inspect", lab.container_id(plan["service"])])
        return out
    if plan["kind"] == "docker_stats":
        argv = ["docker", "stats", "--no-stream"]
        if plan["service"]:
            argv.append(lab.container_id(plan["service"]))
        _, out = lab.run(argv)
        return out
    raise ValueError(f"unknown plan kind {plan['kind']!r}")


def exec_readonly(command: str) -> tuple[str, bool]:
    """Returns (output, is_error)."""
    try:
        plan = validate_exec(command)
        # docker inspect payloads run ~9-10k chars; a 12k cap keeps them whole.
        return truncate(_execute_plan(plan), limit=12000), False
    except Exception as exc:
        return f"error: {exc}", True


def get_logs(service: str, lines: int = 100) -> tuple[str, bool]:
    if service not in lab.SERVICES:
        return f"error: unknown service {service!r}; one of {lab.SERVICES}", True
    lines = max(1, min(int(lines), MAX_LOG_LINES))
    return truncate(lab.compose_logs(service, lines)), False


def get_status() -> tuple[str, bool]:
    return truncate(f"{lab.compose_ps()}\n{lab.api_health()}"), False


TOOL_DEFINITIONS = [
    {
        "name": "get_status",
        "description": (
            "Overview of the stack: docker compose ps for all services plus the "
            "api /health endpoint (checks db and queue connectivity)."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_logs",
        "description": "Recent log lines from one service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": lab.SERVICES,
                    "description": "Which service's logs to read.",
                },
                "lines": {
                    "type": "integer",
                    "description": f"How many trailing lines (default 100, max {MAX_LOG_LINES}).",
                },
            },
            "required": ["service"],
        },
    },
    {
        "name": "probe_connectivity",
        "description": (
            "Check DNS resolution and TCP connectivity from inside one "
            "service's container to another lab service. Proves whether A can "
            "actually reach B on the network, independent of application "
            "code or logs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "from_service": {
                    "type": "string",
                    "enum": PROBE_SOURCES,
                    "description": "Container the probe runs inside.",
                },
                "target": {
                    "type": "string",
                    "description": (
                        "Lab service to probe (postgres, redis, api, nginx), "
                        "optionally with ':port'; defaults to the service's "
                        "standard port."
                    ),
                },
            },
            "required": ["from_service", "target"],
        },
    },
    {
        "name": "exec_readonly",
        "description": (
            "Run one read-only diagnostic command. Allowed forms: "
            "'redis-cli <read-only command>' (e.g. 'redis-cli info memory', "
            "'redis-cli config get maxmemory', 'redis-cli llen jobs'); "
            "'psql SELECT ...' (single read-only SELECT against the shop db); "
            "'docker inspect <service>'; 'docker stats'. Anything else is rejected."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run."},
            },
            "required": ["command"],
        },
    },
]


def dispatch(name: str, tool_input: dict) -> tuple[str, bool]:
    if name == "get_status":
        return get_status()
    if name == "get_logs":
        return get_logs(tool_input.get("service", ""), tool_input.get("lines", 100))
    if name == "exec_readonly":
        return exec_readonly(tool_input.get("command", ""))
    if name == "probe_connectivity":
        return probe_connectivity(
            tool_input.get("from_service", ""), tool_input.get("target", "")
        )
    return f"error: unknown tool {name!r}", True
