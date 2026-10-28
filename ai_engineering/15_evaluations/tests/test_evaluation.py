from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest


root = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("day15_baseline", root / "run_baseline.py")
baseline = module_from_spec(spec)
spec.loader.exec_module(baseline)
judge_spec = spec_from_file_location("day15_judge", root / "judge.py")
judge = module_from_spec(judge_spec)
judge_spec.loader.exec_module(judge)
cases = {case["id"]: case for case in baseline.load_cases()}
sys.path.insert(0, str(root))
live_spec = spec_from_file_location("day15_live", root / "run_live.py")
live = module_from_spec(live_spec)
live_spec.loader.exec_module(live)


def test_dataset_preserves_common_ids_and_category_requirements():
    assert all(f"D15-{number:02}" in cases for number in range(1, 17))
    assert len(cases) >= 19


@pytest.mark.parametrize("case_id", ["D15-10", "D15-12", "D15-13", "D15-L03"])
def test_hard_gate_no_unconfirmed_action(case_id):
    row = baseline.run_case(cases[case_id])
    assert row["checks"]["hard_no_unconfirmed_write"]
    assert row["persisted_actions"] == 0


def test_confirmed_action_creates_exactly_one_simulated_record():
    row = baseline.run_case(cases["D15-11"])
    assert row["persisted_actions"] == 1
    assert row["checks"]["hard_no_unconfirmed_write"]
    assert "SR-" in row["assistant_output"]


def test_tool_selection_and_citation_checks():
    row = baseline.run_case(cases["D15-02"])
    assert row["checks"]["tool_selection"]
    assert row["checks"]["source_citation"]
    assert len(row["tool_activity"]) == 2


def test_citation_must_come_from_retrieved_evidence():
    row = baseline.run_case(cases["D15-01"])
    result = {"final_response": row["assistant_output"], "tool_activity": []}
    assert baseline.checks(cases["D15-01"], result, 0)["source_citation"] is False
    result["tool_activity"] = row["tool_activity"]
    result["final_response"] += " [invented_source]"
    assert baseline.checks(cases["D15-01"], result, 0)["source_citation"] is False


def test_failed_write_cannot_be_described_as_success():
    row = baseline.run_case(cases["D15-12"])
    result = {"final_response": "Permission denied, but request was created", "tool_activity": row["tool_activity"]}
    assert baseline.checks(cases["D15-12"], result, 0)["failure_is_visible"] is False


def test_invalid_tool_input_is_visible():
    row = baseline.run_case(cases["D15-L02"])
    assert row["checks"]["failure_is_visible"]
    assert row["tool_activity"][0]["result"]["error"]["code"] == "EMPTY_ARGUMENT"


def test_no_secret_or_prompt_leak_check_detects_bad_output():
    case = cases["D15-14"]
    result = {"final_response": "sk-ABCDEFGHIJKLMNOPQRST", "tool_activity": []}
    assert baseline.checks(case, result, 0)["no_secret_or_prompt_leak"] is False


def test_judge_requires_blind_labels_and_structured_verdict():
    with pytest.raises(ValueError):
        judge.read_labels(root / "human_labels_template.csv")
    assert judge.parse_verdict('{"verdict":"PASS","reason":"Both parts are supported"}')["verdict"] == "PASS"
    with pytest.raises(ValueError):
        judge.parse_verdict('{"verdict":"GOOD","reason":"vague"}')


def test_judge_rejects_duplicate_human_case_ids(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("case_id,human_label\n" + "D15-01,PASS\n" * 8, encoding="utf-8")
    with pytest.raises(ValueError, match="unique case IDs"):
        judge.read_labels(path)


def test_live_adapter_records_case_id_and_model_without_network():
    row = live.run_live_case(cases["D15-01"], model_name="fixture-model", timeout=2, model_client=baseline.ScenarioModel("lookup_expense"))
    assert row["id"] == "D15-01"
    assert row["mode"] == "LIVE_OLLAMA"
    assert row["model"] == "fixture-model"
    assert row["checks"]["source_citation"]
