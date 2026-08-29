from agent.render import render
from agent.trajectory import TrajectoryWriter


def test_render_produces_readable_markdown(tmp_path):
    writer = TrajectoryWriter("some-case", base_dir=tmp_path)
    writer.log("start", case="some-case", model="claude-test", alert="[ALERT] latency high")
    writer.log("llm_response", step=0, stop_reason="tool_use",
               usage={"input_tokens": 10, "output_tokens": 5}, text="Checking status first.")
    writer.log("tool_call", step=0, name="get_status", input={})
    writer.log("tool_result", step=0, name="get_status", is_error=False, output="all Up\n" * 500)
    writer.log("tool_call", step=1, name="exec_readonly", input={"command": "redis-cli flushall"})
    writer.log("tool_result", step=1, name="exec_readonly", is_error=True,
               output="error: not allowed")
    writer.log("tool_call", step=2, name="submit_diagnosis", input={})
    writer.log("tool_result", step=2, name="submit_diagnosis", is_error=False,
               output="Diagnosis recorded.")
    writer.log("final", n_tool_calls=2, wall_seconds=12.3,
               usage={"input_tokens": 100, "output_tokens": 50},
               answer={"root_cause_component": "redis", "root_cause_type": "misconfiguration",
                       "explanation": "line one\nline two",
                       "evidence": [{"source": "get_status", "quote": "all\nUp"}],
                       "suggested_fix": "raise maxmemory"})

    md = render(writer.path)
    assert "# some-case — run" in md
    assert "## Step 1" in md
    assert "**Agent:** Checking status first." in md
    assert "→ **get_status** `{}`" in md
    assert "chars omitted]" in md            # long results are truncated
    assert "*(tool error)*" in md
    assert "`redis` / `misconfiguration`" in md
    assert "“all Up”" in md                  # quotes are flattened to one line
    assert "2 tool calls · 100 tokens in / 50 out · 12.3s" in md
    assert "submit_diagnosis" not in md      # the answer is shown, not the raw call


def test_render_handles_missing_answer(tmp_path):
    writer = TrajectoryWriter("case-x", base_dir=tmp_path)
    writer.log("start", case="case-x", model="m", alert="a")
    writer.log("final", answer=None, n_tool_calls=0, wall_seconds=1.0, usage={})
    assert "_No diagnosis submitted._" in render(writer.path)
