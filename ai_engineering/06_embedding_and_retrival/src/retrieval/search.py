"""Command-line local similarity search."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
import numpy as np
from src.config import EmbeddingConfig
from src.embeddings.bge_provider import BGEProvider
from src.retrieval.similarity import top_k

def load_index(index_dir: str | Path) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    path = Path(index_dir)
    try:
        vectors = np.load(path / "vectors.npz")["vectors"]
        records = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load embedding index from {path}: {exc}") from exc
    if vectors.ndim != 2 or len(records) != len(vectors) or not len(records):
        raise ValueError("Embedding index has inconsistent or empty vectors and metadata")
    if not np.isfinite(vectors).all():
        raise ValueError("Embedding index contains non-finite vectors")
    return vectors, records, manifest

def search_index(query: str, index_dir: str | Path, k: int = 5, config: EmbeddingConfig | None = None) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("Query cannot be empty")
    vectors, records, manifest = load_index(index_dir)
    config = config or EmbeddingConfig.from_environment()
    if manifest.get("model_id") != config.model_id:
        raise ValueError("Query model does not match the index model")
    if bool(manifest.get("query_instruction_enabled")) != config.use_query_instruction:
        raise ValueError("Query-instruction setting does not match the index")
    provider = BGEProvider(config)
    if vectors.shape[1] != provider.dimension or vectors.shape[1] != int(manifest.get("vector_dimension", -1)):
        raise ValueError("Query and index vector dimensions are incompatible")
    ranked = top_k(provider.embed_query(query), vectors, min(k, len(records)))
    results = []
    for rank, (index, score) in enumerate(ranked, start=1):
        record, metadata = records[index], records[index].get("metadata", {})
        results.append({"rank": rank, "similarity": score, "chunk_id": record.get("chunk_id") or metadata.get("chunk_id"),
                        "text": record.get("text", ""), "metadata": metadata})
    return results

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-dir", required=True)
    parser.add_argument("--query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--export")
    parser.add_argument("--no-query-instruction", action="store_true")
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k must be greater than zero")
    config = EmbeddingConfig.from_environment()
    if args.no_query_instruction:
        config = EmbeddingConfig(**{**config.as_dict(), "use_query_instruction": False})
    if args.query is not None:
        results = search_index(args.query, args.index_dir, args.top_k, config)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        if args.export:
            export = {"query": args.query, "results": results}
            Path(args.export).parent.mkdir(parents=True, exist_ok=True)
            Path(args.export).write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    print("Interactive mode. Press Enter on an empty line to exit.")
    while True:
        query = input("query> ").strip()
        if not query:
            break
        print(json.dumps(search_index(query, args.index_dir, args.top_k, config), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
