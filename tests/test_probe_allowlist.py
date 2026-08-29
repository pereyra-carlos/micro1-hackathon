"""The probe tool is a security boundary too: lab services only, no shell."""

import pytest

from agent.tools import validate_probe


@pytest.mark.parametrize("from_service,target,port", [
    ("api", "postgres", 5432),
    ("api", "redis:6379", 6379),
    ("worker", "postgres:5432", 5432),
    ("nginx", "api", 8000),
    ("postgres", "redis", 6379),
    ("redis", "nginx:80", 80),
])
def test_allowed_probes(from_service, target, port):
    plan = validate_probe(from_service, target)
    assert plan["port"] == port


@pytest.mark.parametrize("from_service,target", [
    ("loadgen", "api"),          # no probe environment; not a source
    ("evil", "postgres"),        # unknown source
    ("api", "worker"),           # worker listens on nothing; not a target
    ("api", "loadgen"),          # not a target
    ("api", "evil.example.com"), # external hosts are out of scope
    ("api", "8.8.8.8"),          # raw IPs too
    ("api", "postgres:abc"),     # non-numeric port
    ("api", "postgres:0"),       # out-of-range port
    ("api", "postgres:70000"),   # out-of-range port
    ("api", "postgres; id"),     # injection attempt
    ("api", ""),
    ("", "postgres"),
])
def test_rejected_probes(from_service, target):
    with pytest.raises(ValueError):
        validate_probe(from_service, target)
