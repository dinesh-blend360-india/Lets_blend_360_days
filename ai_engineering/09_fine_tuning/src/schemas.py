"""Shared schema constants and deterministic validation helpers."""

from __future__ import annotations

from typing import Any


ARCHITECTURES = {
    "PROMPT_CONTEXT", "RAG", "FINE_TUNING", "COMBINATION", "NO_LLM", "DECISION_DEFERRED"
}

SCENARIO_REQUIRED_FIELDS = {
    "scenario_id", "title", "business_scenario", "business_outcome", "problem_type",
    "knowledge_source", "knowledge_freshness", "citation_requirement", "data_availability",
    "privacy_security", "latency_cost_constraints", "reference_architecture",
    "requirements_driving_choice", "why_this_approach", "rejected_alternative",
    "rejected_alternative_reason", "key_risk", "discovery_question", "validation_plan",
    "assumptions_that_could_change_decision", "rubric_keywords",
}

DECISION_CARD_REQUIRED_FIELDS = {
    "scenario_id", "business_outcome", "problem_type", "knowledge_source",
    "knowledge_freshness", "citation_requirement", "data_availability", "privacy_security",
    "latency_cost_constraints", "chosen_approach", "why_this_approach",
    "rejected_alternative", "rejected_alternative_reason", "key_risk",
    "discovery_question", "validation_plan",
}

SUBMISSION_REQUIRED_FIELDS = {
    "scenario_id", "selected_architecture", "reasoning", "rejected_alternative",
    "discovery_question", "validation_plan",
}

SCENARIO_OPTIONAL_FIELDS = {"staged_approach"}
DECISION_CARD_OPTIONAL_FIELDS = {"staged_approach"}
SUBMISSION_OPTIONAL_FIELDS = {"key_risk", "staged_approach"}


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def require_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - set(value))
    if missing:
        raise ValueError(f"{label} is missing required fields: {missing}")
    empty = sorted(field for field in fields if value.get(field) is None or value.get(field) == "")
    if empty:
        raise ValueError(f"{label} has empty required fields: {empty}")


def reject_unknown_fields(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{label} has unsupported fields: {unknown}")


def require_architecture(value: Any, field: str) -> str:
    if value not in ARCHITECTURES:
        raise ValueError(f"{field} must be one of {sorted(ARCHITECTURES)}; got {value!r}")
    return str(value)

