"""Inject a fault case into the running lab: scripts/break.py <case-id>."""

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = REPO_ROOT / "cases" / "cases.yaml"


def load_cases():
    with open(CASES_FILE) as f:
        return {case["id"]: case for case in yaml.safe_load(f)["cases"]}


def inject(case):
    for command in case["injection"]:
        print(f"break: running injection command for {case['id']!r}")
        subprocess.run(command, shell=True, check=True, cwd=REPO_ROOT)


def main():
    cases = load_cases()
    if len(sys.argv) != 2 or sys.argv[1] not in cases:
        print(f"usage: break.py <case-id>  (one of: {', '.join(cases)})", file=sys.stderr)
        return 1
    case = cases[sys.argv[1]]
    inject(case)
    print(f"break: fault {case['id']!r} injected; "
          f"symptoms develop over ~{case['settle_seconds']}s")
    print(f"break: alert text:\n  {case['alert']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
