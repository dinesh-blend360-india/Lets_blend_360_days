import json
import pytest
from src.embeddings.base import load_and_validate_chunks

def test_supports_object_layout_and_generates_stable_id(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps({"chunks": [{"text": "hello", "metadata": {"source": "a.md"}}]}), encoding="utf-8")
    first, _ = load_and_validate_chunks(path)
    second, _ = load_and_validate_chunks(path)
    assert first[0].metadata["chunk_id"] == second[0].metadata["chunk_id"]

def test_rejects_empty_chunk(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps([{"text": "", "metadata": {}}]), encoding="utf-8")
    with pytest.raises(ValueError, match="empty text"):
        load_and_validate_chunks(path)

def test_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps([{"text": "a", "metadata": {"chunk_id": "x"}}, {"text": "b", "metadata": {"chunk_id": "x"}}]), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_and_validate_chunks(path)
