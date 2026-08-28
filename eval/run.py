"""Eval harness: for each case and repetition, reset the lab, inject the
fault, run baseline AND agent on the same broken instance, grade both, and
record accuracy, wall-clock time, and token usage.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from statistics import mean

from agent import run as agent_run
from baseline import run as baseline_run
from common import lab, llm
from eval.grading import grade

RESULTS_DIR = lab.REPO_ROOT / "results"


def _sh(argv):
    subprocess.run(argv, cwd=lab.REPO_ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def reset_and_break(case: dict):
    print(f"eval: resetting lab for case {case['id']!r}...", flush=True)
    _sh(["make", "reset"])
    _sh([sys.executable, "scripts/break.py", case["id"]])
    settle = case["settle_seconds"]
    print(f"eval: fault injected, settling {settle}s...", flush=True)
    time.sleep(settle)


def run_one(case: dict, system: str) -> dict:
    diagnose = baseline_run.diagnose if system == "baseline" else agent_run.diagnose
    result = diagnose(case)
    result["grade"] = grade(result["answer"], case["ground_truth"])
    verdict = "CORRECT" if result["grade"]["correct"] else "WRONG"
    got = (result["answer"] or {}).get("root_cause_component"), \
          (result["answer"] or {}).get("root_cause_type")
    print(f"eval: {system} on {case['id']}: {verdict} "
          f"(answered {got[0]}/{got[1]}, {result['wall_seconds']}s)", flush=True)
    return result


def summarize(rows: list[dict], repetitions: int) -> str:
    lines = [
        "# Eval summary",
        "",
        f"- Model: `{llm.MODEL}`",
        f"- Repetitions per case: {repetitions}",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    keys = sorted({(r["case"], r["system"]) for r in rows},
                  key=lambda k: (k[0], k[1] != "baseline"))
    for case_id, system in keys:
        group = [r for r in rows if r["case"] == case_id and r["system"] == system]
        lines.append(
            f"| {case_id} | {system} "
            f"| {sum(r['grade']['correct'] for r in group)}/{len(group)} "
            f"| {sum(r['grade']['component_match'] for r in group)}/{len(group)} "
            f"| {mean(r['wall_seconds'] for r in group):.1f} "
            f"| {mean(r['usage']['input_tokens'] for r in group):.0f} "
            f"| {mean(r['usage']['output_tokens'] for r in group):.0f} |"
        )
    lines.append("")
    for system in ("baseline", "agent"):
        group = [r for r in rows if r["system"] == system]
        if group:
            lines.append(f"- **{system} overall accuracy: "
                         f"{sum(r['grade']['correct'] for r in group)}/{len(group)}**")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--case", help="run a single case id")
    args = parser.parse_args()

    cases = lab.load_cases()
    if args.case:
        cases = {args.case: cases[args.case]}

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = RESULTS_DIR / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "model": llm.MODEL,
        "repetitions": args.repetitions,
        "cases": list(cases),
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    rows = []
    for case in cases.values():
        for rep in range(args.repetitions):
            print(f"\neval: === case {case['id']} rep {rep + 1}/{args.repetitions} ===",
                  flush=True)
            reset_and_break(case)
            for system in ("baseline", "agent"):
                row = run_one(case, system)
                row["repetition"] = rep
                rows.append(row)
                (out_dir / "results.json").write_text(
                    json.dumps({"meta": meta, "rows": rows}, indent=2, default=str)
                )

    summary = summarize(rows, args.repetitions)
    (out_dir / "summary.md").write_text(summary)
    print(f"\n{summary}")
    print(f"eval: results written to {out_dir.relative_to(lab.REPO_ROOT)}/")
    _sh(["make", "down"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
