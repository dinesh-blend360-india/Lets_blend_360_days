"""Small UI-independent adapter over the existing Day 06 retrieval code.

This module intentionally stops at ranked retrieval. It does not construct
context, call an LLM, or generate an answer.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[2]
DAY06_DIR = PROJECT_DIR / "06_embedding_and_retrieval"
DEFAULT_INDEX_DIR = DAY06_DIR / "outputs" / "embeddings" / "employee_policy_md_structure"


def configured_index_dir(index_dir: str | Path | None = None) -> Path:
    """Resolve a configurable Day 06 index without embedding machine paths."""
    value = index_dir or os.getenv("DAY06_INDEX_DIR")
    path = Path(value) if value else DEFAULT_INDEX_DIR
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def _load_day06_search_module() -> Any:
    """Import Day 06's module in its own package context.

    Day 06 uses the package name ``src``. We put only its project directory at
    the front of sys.path immediately before import, then delegate unchanged.
    """
    if not DAY06_DIR.is_dir():
        raise FileNotFoundError(f"Day 06 project was not found: {DAY06_DIR}")
    day06_text = str(DAY06_DIR)
    if day06_text not in sys.path:
        sys.path.insert(0, day06_text)
    return importlib.import_module("src.retrieval.search")


def inspect_index(index_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the selected Day 06 index and return its manifest summary."""
    module = _load_day06_search_module()
    vectors, records, manifest = module.load_index(configured_index_dir(index_dir))
    return {
        "index_dir": str(configured_index_dir(index_dir)),
        "vector_count": int(len(vectors)),
        "vector_dimension": int(vectors.shape[1]),
        "model_id": manifest.get("model_id"),
        "query_instruction_enabled": manifest.get("query_instruction_enabled"),
        "chunk_ids": [record.get("chunk_id") or record.get("metadata", {}).get("chunk_id") for record in records],
        "manifest": manifest,
    }


def search(
    query: str,
    *,
    index_dir: str | Path | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Return Day 06 ranked results with their original metadata intact."""
    if not query.strip():
        raise ValueError("Query cannot be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    module = _load_day06_search_module()
    # Day 06 search_index validates model ID, vector dimension, and query
    # instruction compatibility against the selected index manifest.
    return module.search_index(query, configured_index_dir(index_dir), k=top_k)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-dir", help="Day 06 index directory; defaults to DAY06_INDEX_DIR or the structure index")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--export", help="Optional JSON output path")
    args = parser.parse_args()
    results = search(args.query, index_dir=args.index_dir, top_k=args.top_k)
    payload = {"query": args.query, "index_dir": str(configured_index_dir(args.index_dir)), "results": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.export:
        output = Path(args.export)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
