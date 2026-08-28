"""Append-only JSONL trajectory log: one file per agent run."""

import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from common.lab import REPO_ROOT

TRAJECTORIES_DIR = REPO_ROOT / "trajectories"


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{secrets.token_hex(2)}"


class TrajectoryWriter:
    def __init__(self, case_id: str, run_id: str | None = None, base_dir: Path = TRAJECTORIES_DIR):
        self.run_id = run_id or new_run_id()
        self.path = Path(base_dir) / case_id / f"{self.run_id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, **fields):
        record = {"ts": round(time.time(), 3), "event": event, **fields}
        with open(self.path, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
