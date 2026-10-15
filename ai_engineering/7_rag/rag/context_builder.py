"""Build bounded, human-readable evidence context from retrieved chunks.

Retrieved text is untrusted evidence. This module formats it as data and never
interprets it as instructions, summarizes it, or generates an answer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class EvidenceRecord:
    """One included evidence block with a traceable source mapping."""

    chunk_id: str
    source: Any
    section: Any
    page: Any
    rank: Any
    similarity: Any
    text: str
    metadata: dict[str, Any]
    formatted_block: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExcludedEvidence:
    """A supplied retrieval result that was not included, with a reason."""

    chunk_id: Any
    reason: str
    required_chars: int | None
    remaining_chars: int
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextBuildResult:
    question: str
    formatted_context: str
    evidence: list[EvidenceRecord]
    excluded: list[ExcludedEvidence]
    max_context_chars: int
    used_context_chars: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "formatted_context": self.formatted_context,
            "evidence": [item.as_dict() for item in self.evidence],
            "excluded": [item.as_dict() for item in self.excluded],
            "max_context_chars": self.max_context_chars,
            "used_context_chars": self.used_context_chars,
        }


def _page_value(metadata: dict[str, Any]) -> Any:
    if metadata.get("page") is not None:
        return metadata["page"]
    start, end = metadata.get("page_start"), metadata.get("page_end")
    if start is not None and end is not None and start != end:
        return f"{start}-{end}"
    return start if start is not None else end if end is not None else "not available"


def _display_value(value: Any) -> str:
    return "not available" if value is None or value == "" else str(value)


def _format_evidence(result: dict[str, Any], metadata: dict[str, Any], text: str) -> str:
    chunk_id = str(result.get("chunk_id"))
    source = metadata.get("source", "not available")
    section = metadata.get("heading_path", "not available")
    page = _page_value(metadata)
    rank = result.get("rank", "not available")
    similarity = result.get("similarity", "not available")
    if isinstance(similarity, float):
        similarity = f"{similarity:.4f}"
    return (
        "[EVIDENCE]\n"
        f"chunk_id: {chunk_id}\n"
        f"source: {_display_value(source)}\n"
        f"section: {_display_value(section)}\n"
        f"page: {_display_value(page)}\n"
        f"rank: {_display_value(rank)}\n"
        f"similarity: {_display_value(similarity)}\n\n"
        "Text:\n"
        f"{text}\n"
        "[/EVIDENCE]"
    )


def build_context(
    question: str,
    retrieved_results: Iterable[dict[str, Any]] | None,
    *,
    max_context_chars: int = 6000,
) -> ContextBuildResult:
    """Format supplied retrieval results into bounded evidence context.

    Evidence blocks are atomic: a block is included in full or excluded in
    full. This avoids silently cutting a sentence or changing the source text.
    Missing IDs/text are excluded instead of being invented or repaired.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question cannot be empty")
    if max_context_chars <= 0:
        raise ValueError("max_context_chars must be greater than zero")

    evidence: list[EvidenceRecord] = []
    excluded: list[ExcludedEvidence] = []
    blocks: list[str] = []
    used = 0
    results = list(retrieved_results or [])

    for index, result in enumerate(results):
        if not isinstance(result, dict):
            excluded.append(ExcludedEvidence(None, "retrieval result is not an object", None, max_context_chars - used, {}))
            continue
        metadata = result.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        chunk_id = result.get("chunk_id") or metadata.get("chunk_id")
        text = result.get("text")
        if not chunk_id:
            excluded.append(ExcludedEvidence(None, "missing chunk_id; IDs are never invented", None, max_context_chars - used, metadata.copy()))
            continue
        if not isinstance(text, str) or not text:
            excluded.append(ExcludedEvidence(str(chunk_id), "missing or empty original text", None, max_context_chars - used, metadata.copy()))
            continue

        block = _format_evidence(result, metadata, text)
        separator_chars = 2 if blocks else 0
        required = len(block) + separator_chars
        remaining = max_context_chars - used
        if required > remaining:
            excluded.append(ExcludedEvidence(str(chunk_id), "would exceed context budget; full block excluded", required, remaining, metadata.copy()))
            continue

        blocks.append(block)
        used += required
        evidence.append(EvidenceRecord(
            chunk_id=str(chunk_id),
            source=metadata.get("source", "not available"),
            section=metadata.get("heading_path", "not available"),
            page=_page_value(metadata),
            rank=result.get("rank", "not available"),
            similarity=result.get("similarity", "not available"),
            text=text,
            metadata=metadata.copy(),
            formatted_block=block,
        ))

    return ContextBuildResult(
        question=question,
        formatted_context="\n\n".join(blocks),
        evidence=evidence,
        excluded=excluded,
        max_context_chars=max_context_chars,
        used_context_chars=used,
    )
