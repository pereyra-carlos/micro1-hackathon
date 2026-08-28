"""The case registry must stay well-formed: grading depends on it."""

from common.diagnosis import COMPONENTS, FAULT_TYPES
from common.lab import SERVICES, load_cases


def test_cases_schema():
    cases = load_cases()
    assert len(cases) >= 2
    for case_id, case in cases.items():
        assert case["id"] == case_id
        assert case["alert"].strip()
        assert case["description"].strip()
        assert case["injection"], f"{case_id}: no injection commands"
        assert case["settle_seconds"] > 0
        truth = case["ground_truth"]
        assert truth["component"] in COMPONENTS
        assert truth["component"] in SERVICES
        assert truth["fault_type"] in FAULT_TYPES
        assert truth["fault_type"] in truth["accepted_fault_types"]
        for fault in truth["accepted_fault_types"]:
            assert fault in FAULT_TYPES


def test_case_ids_are_unique_and_stable():
    assert set(load_cases()) >= {"postgres-down", "redis-oom"}
