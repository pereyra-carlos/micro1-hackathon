"""Automatic grading: structured answer vs the case's canonical root cause."""


def grade(answer: dict | None, ground_truth: dict) -> dict:
    if not answer:
        return {"component_match": False, "fault_match": False, "correct": False}
    component_match = answer.get("root_cause_component") == ground_truth["component"]
    fault_match = answer.get("root_cause_type") in ground_truth["accepted_fault_types"]
    return {
        "component_match": component_match,
        "fault_match": fault_match,
        "correct": component_match and fault_match,
    }
