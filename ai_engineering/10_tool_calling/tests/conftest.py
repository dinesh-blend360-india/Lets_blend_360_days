from pathlib import Path

import pytest

from src.config import AppConfig


@pytest.fixture
def app_config(tmp_path):
    project = Path(__file__).resolve().parents[1]
    ai_dir = project.parent
    return AppConfig(
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="test-model",
        model_timeout_seconds=1,
        max_tool_rounds=3,
        knowledge_backend="mock",
        day07_project_dir=ai_dir / "7_rag",
        day06_index_dir=ai_dir / "6_embedding_and_retrival" / "outputs" / "embeddings" / "employee_policy_md_structure",
        mock_knowledge_file=project / "data" / "mock_knowledge.json",
        actions_dir=tmp_path / "actions",
        log_file=tmp_path / "logs" / "tool_execution.jsonl",
    )

