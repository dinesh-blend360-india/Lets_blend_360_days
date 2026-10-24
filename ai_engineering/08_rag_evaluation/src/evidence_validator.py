"""Dataset, evidence, answer, and failure-stage validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CORPUS_STATUSES = {
    "SUPPORTED_IN_CORPUS", "PARTIALLY_SUPPORTED_IN_CORPUS", "MISSING_FROM_CORPUS", "AMBIGUOUS_SOURCE"
}
FINAL_STATUSES = {"PASS", "FAIL", "BLOCKED_MISSING_SOURCE", "SKIPPED_RUNTIME_UNAVAILABLE", "NEEDS_MANUAL_REVIEW"}
FAILURE_STAGES = {
    "CORPUS_COVERAGE", "RETRIEVAL", "CONTEXT_CONSTRUCTION", "GENERATION_GROUNDING",
    "CITATION_MAPPING", "RUNTIME_OR_CONFIGURATION",
}
REQUIRED_FIELDS = {
    "case_id", "case_type", "question", "expected_evidence_description",
    "expected_relevant_chunk_ids", "expected_facts", "expected_behavior",
    "must_include", "must_not_include", "expected_citations", "corpus_precondition", "evaluation_notes",
}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError("Evaluation dataset must be a non-empty JSON array")
    seen: set[str] = set()
    for index, case in enumerate(value):
        if not isinstance(case, dict):
            raise ValueError(f"Case {index} must be an object")
        missing = sorted(REQUIRED_FIELDS - set(case))
        if missing:
            raise ValueError(f"Case {index} is missing required fields: {missing}")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"Case {index} has an invalid case_id")
        if case_id in seen:
            raise ValueError(f"Duplicate case_id: {case_id}")
        seen.add(case_id)
        if case["corpus_precondition"] not in CORPUS_STATUSES:
            raise ValueError(f"{case_id} has an invalid corpus_precondition")
        for field in ("expected_relevant_chunk_ids", "expected_facts", "must_include", "must_not_include", "expected_citations"):
            if not isinstance(case[field], list):
                raise ValueError(f"{case_id}.{field} must be a list")
        if case["corpus_precondition"] == "MISSING_FROM_CORPUS" and case["expected_relevant_chunk_ids"]:
            raise ValueError(f"{case_id} cannot label relevant chunks when the source is missing")
    return value


def verify_expected_ids(cases: list[dict[str, Any]], metadata_path: str | Path) -> dict[str, Any]:
    records = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    index_ids = {item.get("chunk_id") or item.get("metadata", {}).get("chunk_id") for item in records}
    claimed = {chunk_id for case in cases for chunk_id in case["expected_relevant_chunk_ids"]}
    return {"index_chunk_count": len(index_ids), "verified_ids": sorted(claimed & index_ids), "unknown_ids": sorted(claimed - index_ids)}


def context_evidence_ids(context_record: dict[str, Any]) -> list[str]:
    return [item["chunk_id"] for item in context_record.get("evidence", []) if item.get("chunk_id")]


def validate_citation_ids(generated_ids: list[str], supplied_ids: list[str]) -> dict[str, Any]:
    supplied = set(supplied_ids)
    unknown = sorted(set(generated_ids) - supplied)
    return {"valid": not unknown, "unknown_ids": unknown, "duplicate_ids": sorted({item for item in generated_ids if generated_ids.count(item) > 1})}


def deterministic_answer_checks(case: dict[str, Any], answer: str | None, insufficient: bool | None) -> dict[str, Any]:
    text = (answer or "").casefold()
    missing_terms = [term for term in case["must_include"] if term.casefold() not in text]
    forbidden_terms = [term for term in case["must_not_include"] if term.casefold() in text]
    expected = case["expected_behavior"]
    if expected == "ABSTAIN":
        behavior_ok = insufficient is True
    elif expected == "ANSWER":
        behavior_ok = insufficient is False
    else:
        behavior_ok = None
    return {
        "behavior_ok": behavior_ok,
        "required_terms_present": not missing_terms,
        "missing_required_terms": missing_terms,
        "forbidden_terms_absent": not forbidden_terms,
        "present_forbidden_terms": forbidden_terms,
        "semantic_grounding": "NEEDS_MANUAL_REVIEW",
    }


def classify_failure(*, corpus_status: str, error_stage: str | None, expected_ids: list[str], retrieved_ids: list[str], context_ids: list[str], answer_checks: dict[str, Any], citation_valid: bool) -> tuple[str | None, list[str]]:
    contributing: list[str] = []
    if corpus_status == "MISSING_FROM_CORPUS":
        primary = "CORPUS_COVERAGE"
    elif error_stage:
        primary = error_stage
    elif expected_ids and not set(expected_ids).issubset(retrieved_ids):
        primary = "RETRIEVAL"
    elif expected_ids and not set(expected_ids).issubset(context_ids):
        primary = "CONTEXT_CONSTRUCTION"
    elif not citation_valid:
        primary = "CITATION_MAPPING"
    elif answer_checks.get("behavior_ok") is False or not answer_checks.get("required_terms_present", True) or not answer_checks.get("forbidden_terms_absent", True):
        primary = "GENERATION_GROUNDING"
    else:
        primary = None
    if primary:
        contributing.append(primary)
    if error_stage and error_stage != primary:
        contributing.append(error_stage)
    return primary, contributing

