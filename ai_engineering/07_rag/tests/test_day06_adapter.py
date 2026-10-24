from pathlib import Path

import pytest

from rag import day06_adapter


class FakeDay06Search:
    def search_index(self, query, index_dir, k=5):
        return [{
            "rank": 1,
            "similarity": 0.91,
            "chunk_id": "chunk_existing_1",
            "text": "Original Day 06 text",
            "metadata": {
                "source": "policy.md",
                "page": 2,
                "heading_path": "Travel > Approval",
                "chunk_index": 4,
                "content_type": "paragraph",
            },
        }][:k]

    def load_index(self, index_dir):
        import numpy as np
        return np.zeros((1, 384), dtype=np.float32), [{"chunk_id": "chunk_existing_1", "metadata": {}}], {
            "model_id": "BAAI/bge-small-en-v1.5",
            "query_instruction_enabled": True,
        }


def test_adapter_preserves_day06_result_fields(monkeypatch, tmp_path):
    fake = FakeDay06Search()
    monkeypatch.setattr(day06_adapter, "_load_day06_search_module", lambda: fake)
    results = day06_adapter.search("When is travel approval needed?", index_dir=tmp_path, top_k=3)
    assert results[0]["chunk_id"] == "chunk_existing_1"
    assert results[0]["similarity"] == 0.91
    assert results[0]["metadata"]["heading_path"] == "Travel > Approval"


def test_adapter_rejects_empty_query():
    with pytest.raises(ValueError, match="empty"):
        day06_adapter.search("   ")
