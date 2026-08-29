"""The exec_readonly allowlist is a security boundary: writes must not pass."""

import pytest

from agent.tools import validate_exec


@pytest.mark.parametrize("command", [
    "redis-cli ping",
    "redis-cli info memory",
    "redis-cli INFO errorstats",
    "redis-cli config get maxmemory",
    "redis-cli llen jobs",
    "redis-cli memory stats",
    "psql SELECT count(*) FROM orders",
    "psql -c 'SELECT * FROM reports ORDER BY created_at DESC LIMIT 5'",
    "psql \"select now() - max(created_at) from reports\"",
    "psql SELECT now() - max(created_at) FROM reports",
    "psql SELECT count(*) FROM orders;",
    "docker inspect redis",
    "docker stats",
    "docker stats --no-stream api",
])
def test_allowed_commands(command):
    validate_exec(command)


@pytest.mark.parametrize("command", [
    "",
    "rm -rf /",
    "redis-cli flushall",
    "redis-cli set foo bar",
    "redis-cli config set maxmemory 0",
    "redis-cli shutdown",
    "redis-cli debug sleep 10",
    "redis-cli -h evil.example.com info",
    "psql DROP TABLE orders",
    "psql SELECT 1; DROP TABLE orders",
    "psql SELECT pg_read_file('/etc/passwd') \\! id",
    "psql -U postgres SELECT 1",
    "psql INSERT INTO orders VALUES (99, 'x', 'paid')",
    "docker rm -f incident-lab-api-1",
    "docker inspect some-other-container",
    "docker exec redis sh",
    "docker compose down",
    "curl http://evil.example.com",
])
def test_rejected_commands(command):
    with pytest.raises(ValueError):
        validate_exec(command)


def test_psql_preserves_string_literal_quotes():
    plan = validate_exec("psql SELECT count(*) FROM pg_stat_activity WHERE state != 'idle'")
    assert "'idle'" in plan["sql"]


def test_psql_unwraps_outer_dash_c_quoting():
    plan = validate_exec("psql -c \"SELECT 1 WHERE x = 'a'\"")
    assert plan["sql"] == "SELECT 1 WHERE x = 'a'"


def test_select_into_is_rejected_by_readonly_role_note():
    # SELECT ... INTO would create a table; the psql role 'readonly' has no
    # write grants, so even this residual SELECT form cannot mutate state.
    plan = validate_exec("psql SELECT 1 INTO t")
    assert plan["kind"] == "psql"
