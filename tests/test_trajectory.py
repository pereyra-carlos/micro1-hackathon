import json

from agent.trajectory import TrajectoryWriter


def test_trajectory_is_valid_jsonl(tmp_path):
    writer = TrajectoryWriter("some-case", base_dir=tmp_path)
    writer.log("start", case="some-case")
    writer.log("tool_call", name="get_logs", input={"service": "api"})
    writer.log("final", answer=None)

    lines = writer.path.read_text().splitlines()
    events = [json.loads(line) for line in lines]
    assert [e["event"] for e in events] == ["start", "tool_call", "final"]
    assert all("ts" in e for e in events)
    assert writer.path.parent.name == "some-case"
