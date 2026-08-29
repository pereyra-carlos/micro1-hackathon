"""Render trajectory JSONL files into short readable markdown.

Each trajectories/<case>/<run>.jsonl gets a <run>.md next to it: numbered
steps with the agent's stated reasoning, each tool call with a truncated
result, and the final diagnosis with citations.
"""

import json
import sys
from pathlib import Path

from common.lab import REPO_ROOT

RESULT_PREVIEW_CHARS = 700
QUOTE_PREVIEW_CHARS = 220


def _one_line(text: str, limit: int = QUOTE_PREVIEW_CHARS) -> str:
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[:limit] + "…"


def render(jsonl_path: Path) -> str:
    events = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    lines: list[str] = []
    for event in events:
        kind = event["event"]
        if kind == "start":
            lines += [
                f"# {event['case']} — run {jsonl_path.stem}",
                "",
                f"- model: `{event['model']}`",
                f"- alert: {_one_line(event['alert'], 500)}",
            ]
        elif kind == "llm_response":
            lines += ["", f"## Step {event['step'] + 1}"]
            if event.get("text"):
                lines += ["", f"**Agent:** {event['text'].strip()}"]
        elif kind == "tool_call":
            if event["name"] == "submit_diagnosis":
                continue
            args = json.dumps(event["input"], sort_keys=True)
            lines += ["", f"→ **{event['name']}** `{args}`"]
        elif kind == "tool_result":
            if event["name"] == "submit_diagnosis":
                continue
            output = str(event["output"]).strip()
            if len(output) > RESULT_PREVIEW_CHARS:
                omitted = len(output) - RESULT_PREVIEW_CHARS
                output = output[:RESULT_PREVIEW_CHARS] + f"\n…[{omitted} chars omitted]"
            if event.get("is_error"):
                lines += ["", "*(tool error)*"]
            lines += ["", "```", output, "```"]
        elif kind == "final":
            answer = event.get("answer")
            lines += ["", "## Final diagnosis", ""]
            if not answer:
                lines.append("_No diagnosis submitted._")
            else:
                lines += [
                    f"- **Root cause:** `{answer['root_cause_component']}` / "
                    f"`{answer['root_cause_type']}`",
                    f"- **Explanation:** {_one_line(answer['explanation'], 1200)}",
                    "- **Evidence:**",
                ]
                for item in answer.get("evidence", []):
                    lines.append(
                        f"  - `{_one_line(item['source'], 80)}`: "
                        f"“{_one_line(item['quote'])}”"
                    )
                lines.append(
                    f"- **Suggested fix (advisory):** {_one_line(answer['suggested_fix'], 600)}"
                )
            usage = event.get("usage") or {}
            lines += [
                "",
                f"_{event.get('n_tool_calls', '?')} tool calls · "
                f"{usage.get('input_tokens', '?')} tokens in / "
                f"{usage.get('output_tokens', '?')} out · "
                f"{event.get('wall_seconds', '?')}s_",
            ]
    return "\n".join(lines) + "\n"


def main():
    paths = [Path(p) for p in sys.argv[1:]] or sorted(
        (REPO_ROOT / "trajectories").glob("*/*.jsonl")
    )
    for path in paths:
        path.with_suffix(".md").write_text(render(path))
    print(f"render: wrote {len(paths)} markdown trajectories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
