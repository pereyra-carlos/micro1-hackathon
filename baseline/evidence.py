"""The standard evidence dump the baseline receives: status + recent logs."""

from common import lab
from common.text import truncate

LOG_LINES = 200
PER_SERVICE_LIMIT = 9000


def build_dump() -> str:
    sections = [f"## docker compose ps\n{lab.compose_ps()}"]
    for service in lab.SERVICES:
        logs = truncate(lab.compose_logs(service, LOG_LINES), PER_SERVICE_LIMIT)
        sections.append(f"## last {LOG_LINES} log lines: {service}\n{logs}")
    return "\n\n".join(sections)
