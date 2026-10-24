import json

import pytest

from src.evidence_validator import load_cases


def test_real_dataset_has_eight_unique_cases(tmp_path):
    cases = load_cases("test_inputs/day08_common_cases.json")
    assert len(cases) == 8
    assert len({case["case_id"] for case in cases}) == 8


def test_missing_required_field_is_rejected(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([{"case_id": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        load_cases(path)


def test_duplicate_case_id_is_rejected(tmp_path):
    case = load_cases("test_inputs/day08_common_cases.json")[0]
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([case, case]), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate case_id"):
        load_cases(path)

