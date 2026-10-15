"""Deterministic validation and evidence mapping for generated citations."""

from __future__ import annotations

from typing import Any, Iterable

from rag.answer_generator import GroundedAnswer, INSUFFICIENT_ANSWER
from rag.context_builder import EvidenceRecord


class CitationValidationError(RuntimeError):
    """The model response cannot be safely mapped to supplied evidence."""


def _as_response(value: GroundedAnswer | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, GroundedAnswer):
        return value.as_dict()
    if not isinstance(value, dict):
        raise CitationValidationError("Generator response must be a GroundedAnswer or JSON object")
    return value


def _page_or_none(value: Any) -> Any:
    return None if value == "not available" or value == "" else value


def validate_citations(
    model_response: GroundedAnswer | dict[str, Any],
    evidence: Iterable[EvidenceRecord],
    *,
    retrieved_count: int,
    retrieval_results: Iterable[dict[str, Any]] | None = None,
    include_debug: bool = False,
) -> dict[str, Any]:
    """Validate model IDs and build final citation metadata from evidence only."""
    value = _as_response(model_response)
    answer = value.get("answer")
    insufficient = value.get("insufficient_evidence")
    citations = value.get("citations")
    if not isinstance(answer, str) or not answer.strip():
        raise CitationValidationError("Generated response has no non-empty answer")
    if not isinstance(insufficient, bool) or not isinstance(citations, list):
        raise CitationValidationError("Generated response does not match the answer contract")
    if not all(isinstance(item, str) and item.strip() for item in citations):
        raise CitationValidationError("Citations must be non-empty string chunk IDs")

    evidence_by_id = {record.chunk_id: record for record in evidence}
    supplied_ids = set(evidence_by_id)
    cited_ids: list[str] = []
    for citation_id in citations:
        if citation_id not in supplied_ids:
            raise CitationValidationError(f"Unknown citation ID: {citation_id}")
        if citation_id not in cited_ids:
            cited_ids.append(citation_id)

    if insufficient:
        if cited_ids:
            raise CitationValidationError("Insufficient-evidence responses must have empty citations")
        return _final_response(
            answer=answer.strip() or INSUFFICIENT_ANSWER,
            insufficient=True,
            records=[],
            retrieved_count=retrieved_count,
            retrieval_results=retrieval_results,
            include_debug=include_debug,
        )

    if not cited_ids:
        raise CitationValidationError("Supported factual answers require at least one valid citation")
    return _final_response(
        answer=answer.strip(),
        insufficient=False,
        records=[evidence_by_id[item] for item in cited_ids],
        retrieved_count=retrieved_count,
        retrieval_results=retrieval_results,
        include_debug=include_debug,
    )


def _final_response(
    *,
    answer: str,
    insufficient: bool,
    records: list[EvidenceRecord],
    retrieved_count: int,
    retrieval_results: Iterable[dict[str, Any]] | None,
    include_debug: bool,
) -> dict[str, Any]:
    citations = [
        {
            "chunk_id": record.chunk_id,
            "source": _page_or_none(record.source),
            "heading_path": _page_or_none(record.section),
            "page": _page_or_none(record.page),
        }
        for record in records
    ]
    response: dict[str, Any] = {
        "answer": answer,
        "insufficient_evidence": insufficient,
        "citations": citations,
        "sources": [item["chunk_id"] for item in citations],
    }
    if include_debug:
        response["debug"] = {
            "retrieved_count": retrieved_count,
            "used_chunk_ids": [item["chunk_id"] for item in citations],
            "retrieved": [
                {
                    "chunk_id": item.get("chunk_id"),
                    "rank": item.get("rank"),
                    "similarity": item.get("similarity"),
                }
                for item in (retrieval_results or [])
            ],
        }
    return response
