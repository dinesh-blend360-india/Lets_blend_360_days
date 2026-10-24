"""CLI and orchestration for the eight Day 08 evaluation cases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

from .config import EvaluationConfig
from .evidence_validator import classify_failure, context_evidence_ids, deterministic_answer_checks, load_cases, validate_citation_ids, verify_expected_ids
from .metrics import mean_reciprocal_rank, retrieval_metrics
from .rag_adapter import Day07Adapter
from .report_generator import write_reports


def evaluate_case(case: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    retrieved = runtime.get("retrieved_chunks", [])
    retrieved_ids = [item.get("chunk_id") or item.get("metadata", {}).get("chunk_id") for item in retrieved]
    context = runtime.get("context") or {}
    context_ids = context_evidence_ids(context)
    generated_ids = runtime.get("generated_citation_ids", [])
    citation_check = validate_citation_ids(generated_ids, context_ids)
    missing_expected_citations = sorted(set(case["expected_citations"]) - set(generated_ids))
    citation_check["missing_expected_citations"] = missing_expected_citations
    citation_check["expected_citations_present"] = not missing_expected_citations
    answer_checks = deterministic_answer_checks(case, runtime.get("generated_answer"), runtime.get("insufficient_evidence"))
    error_stage = runtime.get("errors", [{}])[0].get("stage") if runtime.get("errors") else None
    primary, contributing = classify_failure(
        corpus_status=case["corpus_precondition"], error_stage=error_stage,
        expected_ids=case["expected_relevant_chunk_ids"], retrieved_ids=retrieved_ids,
        context_ids=context_ids, answer_checks=answer_checks,
        citation_valid=citation_check["valid"] and citation_check["expected_citations_present"],
    )

    if case["corpus_precondition"] == "MISSING_FROM_CORPUS":
        status = "BLOCKED_MISSING_SOURCE"
    elif error_stage == "RUNTIME_OR_CONFIGURATION" or runtime.get("errors") and runtime["errors"][0]["type"] in {"ModelUnavailableError", "ModuleNotFoundError", "ImportError"}:
        status = "SKIPPED_RUNTIME_UNAVAILABLE"
    elif primary:
        status = "FAIL"
    else:
        status = "NEEDS_MANUAL_REVIEW" if answer_checks["semantic_grounding"] == "NEEDS_MANUAL_REVIEW" else "PASS"

    return {
        "case_id": case["case_id"], "case_type": case["case_type"], "question": case["question"],
        "corpus_precondition": case["corpus_precondition"], "expected_behavior": case["expected_behavior"],
        "expected_evidence_description": case["expected_evidence_description"],
        "expected_relevant_chunk_ids": case["expected_relevant_chunk_ids"],
        "retrieved_ids": retrieved_ids, "retrieved_chunks": retrieved,
        "expected_evidence_found": set(case["expected_relevant_chunk_ids"]).issubset(retrieved_ids) if case["expected_relevant_chunk_ids"] else None,
        "missing_expected_retrieval_ids": sorted(set(case["expected_relevant_chunk_ids"]) - set(retrieved_ids)),
        "retrieval_metrics": retrieval_metrics(retrieved_ids, case["expected_relevant_chunk_ids"]),
        "context_ids": context_ids, "expected_evidence_in_context": set(case["expected_relevant_chunk_ids"]).issubset(context_ids) if case["expected_relevant_chunk_ids"] else None,
        "missing_expected_context_ids": sorted(set(case["expected_relevant_chunk_ids"]) - set(context_ids)),
        "context": context, "answer": runtime.get("generated_answer"),
        "insufficient_evidence": runtime.get("insufficient_evidence"), "citation_ids": generated_ids,
        "validated_citations": runtime.get("validated_citations", []), "citation_validation": citation_check,
        "answer_checks": answer_checks, "status": status, "primary_failure_stage": primary,
        "contributing_failure_stages": contributing, "errors": runtime.get("errors", []),
        "warnings": runtime.get("warnings", []), "runtime_seconds": runtime.get("runtime_seconds"),
        "diagnosis_evidence": case["evaluation_notes"] if primary == "CORPUS_COVERAGE" else "Captured retrieval, context, answer, and citation records are included in this result.",
    }


def run_evaluation(config: EvaluationConfig, *, case_id: str | None = None, adapter_factory: Callable[[EvaluationConfig], Any] = Day07Adapter) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config.validate()
    cases = load_cases(config.cases_file)
    if case_id:
        cases = [case for case in cases if case["case_id"] == case_id]
        if not cases:
            raise ValueError(f"Unknown case_id: {case_id}")
    metadata_path = config.day06_index_dir / "metadata.json"
    evidence_audit = verify_expected_ids(cases, metadata_path)
    if evidence_audit["unknown_ids"]:
        raise ValueError(f"Dataset contains expected IDs absent from the configured index: {evidence_audit['unknown_ids']}")
    adapter = adapter_factory(config)
    results = [evaluate_case(case, adapter.run(case["question"])) for case in cases]
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "config": config.as_dict(),
        "case_count": len(cases), "case_ids": [case["case_id"] for case in cases],
        "evidence_label_audit": evidence_audit, "mrr": mean_reciprocal_rank(results),
        "day07_interface": "rag.day06_adapter.search -> rag.context_builder.build_context -> rag.answer_generator.generate_answer -> rag.citation_validator.validate_citations",
    }
    try:
        manifest["index"] = adapter.inspect()
    except Exception as exc:
        manifest["index_error"] = {"type": type(exc).__name__, "message": str(exc)}
    return results, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", help="Run one stable case ID instead of all cases")
    parser.add_argument("--cases-file")
    parser.add_argument("--output-dir")
    parser.add_argument("--no-write", action="store_true", help="Print results without creating a historical run")
    args = parser.parse_args()
    base = EvaluationConfig.from_environment()
    config = EvaluationConfig(
        day07_project_dir=base.day07_project_dir, day06_index_dir=base.day06_index_dir,
        cases_file=Path(args.cases_file).resolve() if args.cases_file else base.cases_file,
        output_dir=Path(args.output_dir).resolve() if args.output_dir else base.output_dir,
        top_k=base.top_k, max_context_chars=base.max_context_chars,
    )
    results, manifest = run_evaluation(config, case_id=args.case_id)
    if args.no_write:
        print(json.dumps({"manifest": manifest, "results": results}, indent=2, ensure_ascii=False))
    else:
        run_dir = write_reports(config.output_dir, results, manifest)
        print(f"Evaluation artifacts: {run_dir}")


if __name__ == "__main__":
    main()
