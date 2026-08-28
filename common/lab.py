"""Helpers to observe the docker-compose lab (read-only operations only)."""

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO_ROOT / "lab" / "docker-compose.yml"
COMPOSE = ["docker", "compose", "-f", str(COMPOSE_FILE)]
SERVICES = ["nginx", "api", "worker", "postgres", "redis", "loadgen"]

LAB_HTTP_PORT = int(os.environ.get("LAB_HTTP_PORT", "18080"))


def run(argv, timeout=30):
    """Run a command without a shell; return combined stdout+stderr text."""
    proc = subprocess.run(
        argv, cwd=REPO_ROOT, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    return proc.returncode, proc.stdout


def compose_ps() -> str:
    _, out = run(COMPOSE + ["ps", "-a"])
    return out


def compose_logs(service: str, lines: int) -> str:
    _, out = run(COMPOSE + ["logs", "--no-color", "--tail", str(lines), service])
    return out


def container_id(service: str) -> str:
    rc, out = run(COMPOSE + ["ps", "-aq", service])
    if rc != 0 or not out.strip():
        raise ValueError(f"no container found for service {service!r}")
    return out.strip().splitlines()[0]


def api_health() -> str:
    """GET /health through nginx, the same path a real probe would take."""
    url = f"http://localhost:{LAB_HTTP_PORT}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return f"GET /health -> {resp.status} {resp.read().decode()}"
    except urllib.error.HTTPError as exc:
        return f"GET /health -> {exc.code} {exc.read().decode()}"
    except Exception as exc:
        return f"GET /health failed: {exc}"


def load_cases() -> dict:
    import yaml

    with open(REPO_ROOT / "cases" / "cases.yaml") as f:
        return {case["id"]: case for case in yaml.safe_load(f)["cases"]}
