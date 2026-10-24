"""Phase 4 retrieval-to-grounded-response orchestration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from rag.answer_generator import GroundedAnswer, OllamaConfig, generate_answer, INSUFFICIENT_ANSWER
from rag.citation_validator import validate_citations
from rag.context_builder import ContextBuildResult, build_context
from rag.day06_adapter import search


def run_rag(
    question: str,
    *,
    index_dir: str | Path | None = None,
    top_k: int = 5,
    max_context_chars: int = 6000,
    include_debug: bool = False,
    ollama_config: OllamaConfig | None = None,
    retriever: Callable[..., list[dict[str, Any]]] | None = None,
    generator: Callable[..., GroundedAnswer | dict[str, Any]] | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run retrieval, context construction, generation, and citation validation."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question cannot be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    retriever = retriever or search
    generator = generator or generate_answer
    retrieved = retriever(question, index_dir=index_dir, top_k=top_k)
    context: ContextBuildResult = build_context(question, retrieved, max_context_chars=max_context_chars)

    if not context.evidence:
        response: dict[str, Any] = {
            "answer": INSUFFICIENT_ANSWER,
            "insufficient_evidence": True,
            "citations": [],
            "sources": [],
        }
        if include_debug:
            response["debug"] = {
                "retrieved_count": len(retrieved),
                "used_chunk_ids": [],
                "retrieved": [
                    {"chunk_id": item.get("chunk_id"), "rank": item.get("rank"), "similarity": item.get("similarity")}
                    for item in retrieved
                ],
            }
        return response

    generated = generator(
        question,
        context.formatted_context,
        [record.chunk_id for record in context.evidence],
        config=ollama_config,
        client=client,
    )
    return validate_citations(
        generated,
        context.evidence,
        retrieved_count=len(retrieved),
        retrieval_results=retrieved,
        include_debug=include_debug,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True)
    parser.add_argument("--index-dir")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-context-chars", type=int, default=6000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    response = run_rag(
        args.question,
        index_dir=args.index_dir,
        top_k=args.top_k,
        max_context_chars=args.max_context_chars,
        include_debug=args.debug,
    )
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
