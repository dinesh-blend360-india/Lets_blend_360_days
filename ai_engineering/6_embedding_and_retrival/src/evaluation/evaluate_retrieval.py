"""Evaluate Recall@K and MRR using editable, source-grounded queries."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from src.config import EmbeddingConfig
from src.retrieval.search import load_index, search_index

def _resolve_expected(query: dict[str, Any], records: list[dict[str, Any]]) -> tuple[set[str], str | None]:
    ids = {str(value) for value in query.get("expected_chunk_ids", [])}
    contains = query.get("expected_text_contains", [])
    if isinstance(contains, str):
        contains = [contains]
    for phrase in contains:
        ids.update(str(r.get("chunk_id") or r.get("metadata", {}).get("chunk_id")) for r in records if str(phrase).lower() in str(r.get("text", "")).lower())
    if not ids:
        return set(), "no expected source passage matched the index"
    known = {str(r.get("chunk_id") or r.get("metadata", {}).get("chunk_id")) for r in records}
    missing = ids - known
    return ids & known, (f"expected chunk IDs not present: {sorted(missing)}" if missing else None)

def evaluate(query_path: str | Path, index_dir: str | Path, top_k_values: tuple[int, ...] = (1, 3, 5), config: EmbeddingConfig | None = None) -> dict[str, Any]:
    queries = json.loads(Path(query_path).read_text(encoding="utf-8"))
    if not isinstance(queries, list):
        raise ValueError("Retrieval queries JSON must be a list")
    _, records, _ = load_index(index_dir)
    config = config or EmbeddingConfig.from_environment()
    details, reciprocal_ranks = [], []
    counts = {f"recall_at_{k}": 0 for k in top_k_values}
    no_source = 0
    for query in queries:
        expected, note = _resolve_expected(query, records)
        if not expected:
            no_source += 1
            details.append({"query": query.get("query", ""), "status": "no_relevant_source_passage", "note": note})
            continue
        results = search_index(str(query.get("query", "")), index_dir, max(top_k_values), config)
        result_ids = [str(r["chunk_id"]) for r in results]
        first_rank = next((rank for rank, item in enumerate(result_ids, 1) if item in expected), None)
        reciprocal_ranks.append(1 / first_rank if first_rank else 0.0)
        for k in top_k_values:
            counts[f"recall_at_{k}"] += int(bool(expected.intersection(result_ids[:k])))
        details.append({"query": query.get("query", ""), "expected_chunk_ids": sorted(expected), "results": results, "first_relevant_rank": first_rank})
    evaluated = len(reciprocal_ranks)
    metrics = {key: (value / evaluated if evaluated else 0.0) for key, value in counts.items()}
    metrics["mrr"] = sum(reciprocal_ranks) / evaluated if evaluated else 0.0
    return {"index_dir": str(Path(index_dir).resolve()), "query_file": str(Path(query_path).resolve()),
            "queries_total": len(queries), "queries_evaluated": evaluated, "queries_without_relevant_source": no_source,
            "queries_with_no_relevant_result_retrieved": sum(1 for d in details if d.get("first_relevant_rank") is None and d.get("status") is None),
            "metrics": metrics, "details": details}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--index-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-query-instruction", action="store_true")
    args = parser.parse_args()
    config = EmbeddingConfig.from_environment()
    if args.no_query_instruction:
        config = EmbeddingConfig(**{**config.as_dict(), "use_query_instruction": False})
    report = evaluate(args.queries, args.index_dir, config=config)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"], indent=2))

if __name__ == "__main__":
    main()
