import os

import pytest

from src.config import EvaluationConfig
from src.rag_adapter import Day07Adapter


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DAY08_INTEGRATION") != "1", reason="set RUN_DAY08_INTEGRATION=1 to use the real index and Ollama")
def test_real_receipt_threshold_pipeline():
    config = EvaluationConfig.from_environment()
    result = Day07Adapter(config).run("What is the exact monetary threshold above which receipts are required?")
    assert not result["errors"]
    assert "chunk_5762afc8dde2640e56dd" in [item["chunk_id"] for item in result["retrieved_chunks"]]
    assert result["final_response"] is not None

