import json
from pathlib import Path

from rag.phase5_runner import run_cases


def test_phase5_case_file_has_required_cases():
    path = Path(__file__).resolve().parents[1] / "test_inputs" / "rag_test_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    assert len(cases) >= 13
    ids = {case["id"] for case in cases}
    assert {"direct_expense_deadline", "receipt_threshold", "hotel_spending_limit", "generation_failure", "instruction_injection"} <= ids


def test_known_expected_ids_exist_in_real_day06_index():
    cases_path = Path(__file__).resolve().parents[1] / "test_inputs" / "rag_test_cases.json"
    metadata_path = Path(__file__).resolve().parents[3] / "6_embedding_and_retrival" / "outputs" / "embeddings" / "employee_policy_md_structure" / "metadata.json"
    if not metadata_path.is_file():
        return
    records = json.loads(metadata_path.read_text(encoding="utf-8"))
    actual_ids = {record.get("chunk_id") or record.get("metadata", {}).get("chunk_id") for record in records}
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    expected_ids = {chunk_id for case in cases for chunk_id in case.get("expected_evidence_ids", [])}
    assert expected_ids <= actual_ids


def test_mocked_phase5_runner_passes_all_cases(tmp_path):
    path = Path(__file__).resolve().parents[1] / "test_inputs" / "rag_test_cases.json"
    report = run_cases(path, tmp_path / "phase5_results.json")
    assert report["mode"] == "mocked"
    assert report["case_count"] == 13
    assert report["failed_count"] == 0
    assert all(item["passed"] for item in report["results"])
