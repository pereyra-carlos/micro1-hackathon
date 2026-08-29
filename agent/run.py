"""Agent v0: a minimal tool-use loop with read-only investigation tools.

Every step (LLM call, tool call, truncated tool result, token usage) is
appended to trajectories/<case>/<run-id>.jsonl.
"""

import json
import sys
import time

from agent import tools
from agent.trajectory import TrajectoryWriter
from common import lab, llm
from common.diagnosis import DIAGNOSIS_TOOL

MAX_LLM_CALLS = 12

SYSTEM = f"""\
You are an SRE incident copilot investigating a production incident in a
docker-compose stack: nginx fronts a FastAPI api; the api uses postgres and
enqueues jobs on a redis list; a worker consumes the queue and writes reports
to postgres. A load generator provides steady traffic.

You receive an alert. Investigate with the read-only tools.

Method:
- Start from the symptom, then walk the dependency chain; the root cause is
  often not in the alerted service.
- Form an explicit hypothesis and pick the tool call that best discriminates
  it; do not re-request evidence you already have.
- Symptoms are not causes: keep digging until you find a state or
  configuration that explains the whole causal chain.
- Logs can be silent about the cause. The absence of errors in a service does
  not clear its dependencies -- inspect their state directly (redis INFO and
  CONFIG GET, SQL queries, docker inspect).

You have a budget of at most {MAX_LLM_CALLS} investigation steps. When you can
explain the causal chain, call submit_diagnosis exactly once. Evidence must be
verbatim quotes from your tool outputs, each labeled with the tool call that
produced it. The suggested fix is advisory: a human reviews it and nothing is
ever executed automatically."""

WRAP_UP = (
    "You are out of investigation budget. Call submit_diagnosis now with your "
    "best-supported conclusion."
)
NUDGE = "Continue: investigate with your tools, or call submit_diagnosis if done."


def diagnose(case: dict, run_id: str | None = None) -> dict:
    start = time.monotonic()
    trajectory = TrajectoryWriter(case["id"], run_id)
    trajectory.log("start", case=case["id"], model=llm.MODEL, alert=case["alert"])

    api = llm.client()
    messages = [{
        "role": "user",
        "content": f"Incident alert:\n{case['alert']}\n\nInvestigate and diagnose the root cause.",
    }]
    tool_defs = tools.TOOL_DEFINITIONS + [DIAGNOSIS_TOOL]

    usage = {}
    answer = None
    n_tool_calls = 0
    for step in range(MAX_LLM_CALLS):
        if step == MAX_LLM_CALLS - 1:
            messages.append({"role": "user", "content": WRAP_UP})
        response = api.messages.create(
            model=llm.MODEL,
            max_tokens=llm.MAX_TOKENS,
            system=SYSTEM,
            tools=tool_defs,
            messages=messages,
        )
        usage = llm.add_usage(usage, llm.usage_dict(response))
        text = " ".join(b.text for b in response.content if b.type == "text")
        trajectory.log("llm_response", step=step, stop_reason=response.stop_reason,
                       usage=llm.usage_dict(response), text=text)

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})
        if not tool_uses:
            # The model answered in prose; nudge it back onto the contract.
            messages.append({"role": "user", "content": NUDGE})
            continue

        results = []
        for block in tool_uses:
            trajectory.log("tool_call", step=step, name=block.name, input=block.input)
            if block.name == "submit_diagnosis":
                answer = block.input
                output, is_error = "Diagnosis recorded.", False
            else:
                n_tool_calls += 1
                output, is_error = tools.dispatch(block.name, block.input)
            trajectory.log("tool_result", step=step, name=block.name,
                           is_error=is_error, output=output)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
                **({"is_error": True} if is_error else {}),
            })
        messages.append({"role": "user", "content": results})
        if answer is not None:
            break

    result = {
        "system": "agent",
        "case": case["id"],
        "model": llm.MODEL,
        "run_id": trajectory.run_id,
        "answer": answer,
        "usage": usage,
        "n_tool_calls": n_tool_calls,
        "wall_seconds": round(time.monotonic() - start, 1),
        "trajectory": str(trajectory.path.relative_to(lab.REPO_ROOT)),
    }
    trajectory.log("final", answer=answer, usage=usage,
                   n_tool_calls=n_tool_calls, wall_seconds=result["wall_seconds"])
    return result


def main():
    cases = lab.load_cases()
    if len(sys.argv) != 2 or sys.argv[1] not in cases:
        print(f"usage: python -m agent.run <case-id>  (one of: {', '.join(cases)})",
              file=sys.stderr)
        return 1
    print(json.dumps(diagnose(cases[sys.argv[1]]), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
