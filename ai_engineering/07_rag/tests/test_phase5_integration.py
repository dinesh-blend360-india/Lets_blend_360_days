import os
from pathlib import Path

import pytest

from rag.pipeline import run_rag


pytestmark = pytest.mark.integration


@pytest.mark.skipif(os.getenv("RUN_RAG_INTEGRATION") != "1", reason="Set RUN_RAG_INTEGRATION=1 to run local-index/Ollama integration")
def test_real_day06_index_and_ollama_end_to_end():
    index = Path(__file__).resolve().parents[2] / "06_embedding_and_retrieval" / "outputs" / "embeddings" / "employee_policy_md_structure"
    if not (index / "manifest.json").is_file():
        pytest.skip("Real Day 06 structure index is unavailable")
    result = run_rag("When is a receipt required?", index_dir=index, top_k=5, include_debug=True)
    assert isinstance(result["answer"], str)
    assert result["insufficient_evidence"] is False
    assert result["citations"]
    assert result["sources"] == [item["chunk_id"] for item in result["citations"]]
