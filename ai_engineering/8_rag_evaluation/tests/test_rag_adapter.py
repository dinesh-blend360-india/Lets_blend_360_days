from pathlib import Path

from src.config import EvaluationConfig
from src.evaluator import evaluate_case, run_evaluation


def _case(corpus="SUPPORTED_IN_CORPUS"):
    return {
        "case_id": "receipt", "case_type": "numeric", "question": "threshold?",
        "expected_evidence_description": "receipt threshold", "expected_relevant_chunk_ids": ["chunk"] if corpus != "MISSING_FROM_CORPUS" else [],
        "expected_facts": ["500"], "expected_behavior": "ANSWER" if corpus != "MISSING_FROM_CORPUS" else "ABSTAIN",
        "must_include": ["500"] if corpus != "MISSING_FROM_CORPUS" else ["Insufficient evidence"],
        "must_not_include": [], "expected_citations": ["chunk"] if corpus != "MISSING_FROM_CORPUS" else [],
        "corpus_precondition": corpus, "evaluation_notes": "mock",
    }


def test_normalized_mock_pipeline_passes_deterministic_checks():
    runtime = {
        "retrieved_chunks": [{"chunk_id": "chunk", "rank": 1, "similarity": 0.9}],
        "context": {"evidence": [{"chunk_id": "chunk"}], "formatted_context": "evidence"},
        "generated_answer": "Receipts are required at 500 currency units or more.",
        "insufficient_evidence": False, "generated_citation_ids": ["chunk"],
        "validated_citations": [{"chunk_id": "chunk"}], "errors": [], "warnings": [], "runtime_seconds": 0.01,
    }
    result = evaluate_case(_case(), runtime)
    assert result["retrieval_metrics"]["recall_at_1"] == 1.0
    assert result["primary_failure_stage"] is None
    assert result["status"] == "NEEDS_MANUAL_REVIEW"


def test_runtime_failure_is_skipped_for_supported_case():
    runtime = {"errors": [{"stage": "RUNTIME_OR_CONFIGURATION", "type": "ModuleNotFoundError", "message": "missing"}]}
    assert evaluate_case(_case(), runtime)["status"] == "SKIPPED_RUNTIME_UNAVAILABLE"


def test_missing_source_remains_blocked_even_with_correct_abstention():
    runtime = {"generated_answer": "Insufficient evidence", "insufficient_evidence": True, "generated_citation_ids": [], "errors": [], "retrieved_chunks": [], "context": {"evidence": []}}
    result = evaluate_case(_case("MISSING_FROM_CORPUS"), runtime)
    assert result["status"] == "BLOCKED_MISSING_SOURCE"
    assert result["primary_failure_stage"] == "CORPUS_COVERAGE"


def test_expected_citation_is_required_not_just_any_supplied_id():
    runtime = {
        "retrieved_chunks": [{"chunk_id": "chunk"}, {"chunk_id": "unrelated"}],
        "context": {"evidence": [{"chunk_id": "chunk"}, {"chunk_id": "unrelated"}]},
        "generated_answer": "The threshold is 500.", "insufficient_evidence": False,
        "generated_citation_ids": ["unrelated"], "validated_citations": [{"chunk_id": "unrelated"}],
        "errors": [], "warnings": [],
    }
    result = evaluate_case(_case(), runtime)
    assert result["status"] == "FAIL"
    assert result["primary_failure_stage"] == "CITATION_MAPPING"

