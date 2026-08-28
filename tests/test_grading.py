from eval.grading import grade

TRUTH = {
    "component": "redis",
    "fault_type": "resource_exhaustion",
    "accepted_fault_types": ["resource_exhaustion", "misconfiguration"],
}


def answer(component, fault):
    return {"root_cause_component": component, "root_cause_type": fault}


def test_exact_match_is_correct():
    assert grade(answer("redis", "resource_exhaustion"), TRUTH)["correct"]


def test_accepted_synonym_fault_type_is_correct():
    assert grade(answer("redis", "misconfiguration"), TRUTH)["correct"]


def test_wrong_component_fails_even_with_right_fault_type():
    result = grade(answer("api", "resource_exhaustion"), TRUTH)
    assert not result["correct"]
    assert not result["component_match"]
    assert result["fault_match"]


def test_wrong_fault_type_fails_even_with_right_component():
    result = grade(answer("redis", "process_down"), TRUTH)
    assert not result["correct"]
    assert result["component_match"]


def test_missing_answer_fails():
    assert not grade(None, TRUTH)["correct"]
    assert not grade({}, TRUTH)["correct"]
