"""Build a local, traceable NumPy embedding index from Day 05 chunks."""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import numpy as np
from src.config import EmbeddingConfig
from src.embeddings.base import ValidatedChunk, load_and_validate_chunks
from src.embeddings.bge_provider import BGEProvider

def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _load_cache(index_dir: Path, config: EmbeddingConfig, chunks: list[ValidatedChunk]) -> tuple[dict[str, np.ndarray], int]:
    manifest_path, vectors_path, metadata_path = index_dir / "manifest.json", index_dir / "vectors.npz", index_dir / "metadata.json"
    if not (manifest_path.is_file() and vectors_path.is_file() and metadata_path.is_file()):
        return {}, 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("model_id") != config.model_id or manifest.get("embedding_config") != config.as_dict():
            return {}, 0
        old_records = json.loads(metadata_path.read_text(encoding="utf-8"))
        old_vectors = np.load(vectors_path)["vectors"]
        if len(old_records) != len(old_vectors):
            return {}, 0
        allowed = {c.metadata["chunk_id"] for c in chunks}
        cache = {r["chunk_id"]: old_vectors[i] for i, r in enumerate(old_records) if r.get("chunk_id") in allowed}
        return cache, len(cache)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return {}, 0

def build_index(input_path: str | Path, index_dir: str | Path, config: EmbeddingConfig | None = None) -> dict[str, Any]:
    config = config or EmbeddingConfig.from_environment()
    if config.batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    chunks, input_hash = load_and_validate_chunks(input_path)
    index_path = Path(index_dir)
    provider = BGEProvider(config)
    cache, reused = _load_cache(index_path, config, chunks)
    lengths = provider.token_lengths([chunk.text for chunk in chunks])
    too_long = [{"chunk_id": c.metadata["chunk_id"], "token_count": length, "max_seq_length": provider.max_seq_length,
                 "reason": "exceeds_model_token_limit"} for c, length in zip(chunks, lengths) if length and length > provider.max_seq_length]
    skipped_ids = {item["chunk_id"] for item in too_long}
    active = [c for c in chunks if c.metadata["chunk_id"] not in skipped_ids]
    missing = [c for c in active if c.metadata["chunk_id"] not in cache]
    new_vectors = provider.embed_documents([c.text for c in missing])
    vectors_by_id = dict(cache)
    for chunk, vector in zip(missing, new_vectors):
        vectors_by_id[chunk.metadata["chunk_id"]] = vector
    if not active:
        raise ValueError("All chunks were skipped because they exceed the model token limit")
    vectors = np.vstack([vectors_by_id[c.metadata["chunk_id"]] for c in active]).astype(np.float32)
    if vectors.shape != (len(active), provider.dimension) or not np.isfinite(vectors).all():
        raise ValueError("Stored vectors are invalid or misaligned with chunks")
    records = [c.as_metadata_record() for c in active]
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "input_file": str(Path(input_path).resolve()),
        "input_file_sha256": input_hash, "model_id": provider.model_id, "embedding_config": config.as_dict(),
        "vector_dimension": provider.dimension, "max_seq_length": provider.max_seq_length, "normalized": config.normalize,
        "query_instruction_enabled": config.use_query_instruction,
        "query_instruction": config.query_instruction if config.use_query_instruction else "",
        "chunk_count_input": len(chunks), "chunk_count_indexed": len(active), "reused_from_cache": reused,
        "newly_embedded": len(missing), "skipped_count": len(too_long), "skipped_chunks": too_long,
        "source_hashes": sorted({c.source_hash for c in active})}
    index_path.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(index_path / "vectors.npz", vectors=vectors)
    _write_json(index_path / "metadata.json", records)
    _write_json(index_path / "manifest.json", manifest)
    return manifest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Day 05 chunked JSON file")
    parser.add_argument("--index-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--no-query-instruction", action="store_true")
    args = parser.parse_args()
    config = EmbeddingConfig.from_environment()
    if args.batch_size is not None:
        config = EmbeddingConfig(**{**config.as_dict(), "batch_size": args.batch_size})
    if args.no_query_instruction:
        config = EmbeddingConfig(**{**config.as_dict(), "use_query_instruction": False})
    print(json.dumps(build_index(args.input, args.index_dir, config), indent=2))

if __name__ == "__main__":
    main()
