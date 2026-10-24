"""Provider interface and input validation shared by embedding backends."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol, Sequence

class EmbeddingProvider(Protocol):
    model_id: str
    dimension: int
    max_seq_length: int
    def embed_documents(self, texts: Sequence[str]) -> Any: ...
    def embed_query(self, text: str) -> Any: ...

@dataclass
class ValidatedChunk:
    text: str
    metadata: dict[str, Any]
    source_hash: str
    content_hash: str
    source_is_day05: bool = True

    def as_metadata_record(self) -> dict[str, Any]:
        return {"chunk_id": self.metadata["chunk_id"], "text": self.text, "metadata": self.metadata,
                "source_hash": self.source_hash, "content_hash": self.content_hash,
                "source_is_day05": self.source_is_day05}

def stable_chunk_id(source: str, metadata: dict[str, Any], text: str) -> str:
    identity = {"source": source, "page": metadata.get("page", metadata.get("page_start")),
                "chunk_index": metadata.get("chunk_index"), "global_chunk_index": metadata.get("global_chunk_index"),
                "text": text}
    payload = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "chunk_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]

def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_and_validate_chunks(input_path: str | Path) -> tuple[list[ValidatedChunk], str]:
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"Chunk input does not exist: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Chunk input is not valid JSON: {path}: {exc}") from exc
    records = raw if isinstance(raw, list) else raw.get("chunks") if isinstance(raw, dict) else None
    if not isinstance(records, list) or not records:
        raise ValueError("Chunk input must be a non-empty JSON list or an object with a non-empty 'chunks' list")
    chunks: list[ValidatedChunk] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Chunk {index} is not an object")
        text = str(record.get("text", "")).strip()
        if not text:
            raise ValueError(f"Chunk {index} has empty text")
        original_metadata = record.get("metadata") or {}
        if not isinstance(original_metadata, dict):
            raise ValueError(f"Chunk {index} metadata must be an object")
        metadata = dict(original_metadata)
        source = str(metadata.get("source", "unknown-source"))
        existing_id = metadata.get("chunk_id") or record.get("chunk_id")
        chunk_id = str(existing_id) if existing_id else stable_chunk_id(source, metadata, text)
        if chunk_id in seen:
            raise ValueError(f"Duplicate chunk_id before embedding: {chunk_id}")
        seen.add(chunk_id)
        metadata["chunk_id"] = chunk_id
        metadata.setdefault("chunk_index", index)
        metadata.setdefault("content_type", "unknown")
        chunks.append(ValidatedChunk(text, metadata, _hash_text(source), _hash_text(text), bool(original_metadata)))
    input_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    return chunks, input_hash
