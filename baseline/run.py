"""Baseline: ONE Claude call over a standard evidence dump.

Frozen by design after the first eval run -- the agent is measured against
this fixed reference, so nothing here may be tuned later.
"""

import json
import sys
import time

from baseline.evidence import build_dump
from common import lab, llm
from common.diagnosis import DIAGNOSIS_TOOL

SYSTEM = """\
You are an expert SRE performing root-cause analysis of a production incident.

You receive an alert and a standard evidence bundle: service status plus the
most recent log lines of every service in the stack (nginx -> api -> postgres,
and a redis queue consumed by a worker that writes reports to postgres).

Work carefully:
- Correlate symptoms across services and distinguish symptoms from causes.
- The alerted service is often NOT where the root cause lives.
- If no log states the cause directly, reason about which failure mode in
  which component would produce exactly this combination of symptoms and
  silences, and commit to the most likely one.

Finish by calling submit_diagnosis exactly once. Cite evidence as verbatim
quotes from the bundle, naming the section each quote comes from. The
suggested fix is advisory: a human reviews it before anything is executed."""

NUDGE = "Now call submit_diagnosis exactly once with your final diagnosis."


def diagnose(case: dict) -> dict:
    start = time.monotonic()
    dump = build_dump()
    messages = [{
        "role": "user",
        "content": (
            f"Incident alert:\n{case['alert']}\n\n"
            f"Evidence bundle:\n{dump}\n\n"
            "Diagnose the root cause and call submit_diagnosis."
        ),
    }]

    api = llm.client()
    usage = {}
    answer = None
    for _ in range(2):  # one call, plus one nudge if the model answered in prose
        response = api.messages.create(
            model=llm.MODEL,
            max_tokens=llm.MAX_TOKENS,
            system=SYSTEM,
            tools=[DIAGNOSIS_TOOL],
            messages=messages,
        )
        usage = llm.add_usage(usage, llm.usage_dict(response))
        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is not None:
            answer = tool_use.input
            break
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": NUDGE})

    return {
        "system": "baseline",
        "case": case["id"],
        "model": llm.MODEL,
        "answer": answer,
        "usage": usage,
        "wall_seconds": round(time.monotonic() - start, 1),
    }


def main():
    cases = lab.load_cases()
    if len(sys.argv) != 2 or sys.argv[1] not in cases:
        print(f"usage: python -m baseline.run <case-id>  (one of: {', '.join(cases)})",
              file=sys.stderr)
        return 1
    print(json.dumps(diagnose(cases[sys.argv[1]]), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
