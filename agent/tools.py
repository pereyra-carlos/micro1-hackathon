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
        return _validate_psql(shlex.split(command)[1:])
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


def _validate_psql(args) -> dict:
    if args and args[0] == "-c":
        args = args[1:]
    # Only the first token could act as a psql flag; later '-' tokens are SQL
    # arithmetic, and the whole tail is passed as a single -c string anyway.
    if args and args[0].startswith("-"):
        raise ValueError("psql flags are not allowed; pass 'psql SELECT ...'")
    sql = " ".join(args).strip()
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
        return truncate(_execute_plan(plan)), False
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
    return f"error: unknown tool {name!r}", True
