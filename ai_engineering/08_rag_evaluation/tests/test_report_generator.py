from src.report_generator import write_reports


def test_report_history_is_not_overwritten(tmp_path):
    results = [{"case_id": "x", "question": "q", "corpus_precondition": "MISSING_FROM_CORPUS", "status": "BLOCKED_MISSING_SOURCE", "primary_failure_stage": "CORPUS_COVERAGE", "contributing_failure_stages": ["CORPUS_COVERAGE"], "retrieved_ids": [], "context_ids": [], "answer": None, "insufficient_evidence": None, "citation_ids": [], "diagnosis_evidence": "missing"}]
    run_dir = write_reports(tmp_path, results, {"test": True}, run_id="fixed")
    assert (run_dir / "results.json").is_file()
    assert (run_dir / "results.csv").is_file()
    assert (run_dir / "summary.md").is_file()
    assert (tmp_path / "summaries" / "latest_summary.md").is_file()
    try:
        write_reports(tmp_path, results, {}, run_id="fixed")
        assert False, "expected historical run protection"
    except FileExistsError:
        pass

