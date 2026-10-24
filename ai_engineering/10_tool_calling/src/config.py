"""Application-owned configuration and authorization context."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
AI_ENGINEERING_DIR = PROJECT_DIR.parent


def _path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    path = Path(value) if value else default
    return path if path.is_absolute() else (PROJECT_DIR / path).resolve()


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    can_create_service_request: bool


@dataclass(frozen=True)
class AppConfig:
    ollama_base_url: str
    ollama_model: str
    model_timeout_seconds: float
    max_tool_rounds: int
    knowledge_backend: str
    day07_project_dir: Path
    day06_index_dir: Path
    mock_knowledge_file: Path
    actions_dir: Path
    log_file: Path

    @classmethod
    def from_environment(cls) -> "AppConfig":
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            model_timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
            max_tool_rounds=int(os.getenv("MAX_TOOL_ROUNDS", "3")),
            knowledge_backend=os.getenv("KNOWLEDGE_BACKEND", "day07").lower(),
            day07_project_dir=_path("DAY07_PROJECT_DIR", AI_ENGINEERING_DIR / "7_rag"),
            day06_index_dir=_path("DAY06_INDEX_DIR", AI_ENGINEERING_DIR / "6_embedding_and_retrival" / "outputs" / "embeddings" / "employee_policy_md_structure"),
            mock_knowledge_file=_path("MOCK_KNOWLEDGE_FILE", PROJECT_DIR / "data" / "mock_knowledge.json"),
            actions_dir=_path("SERVICE_REQUEST_DIR", PROJECT_DIR / "outputs" / "actions"),
            log_file=_path("TOOL_LOG_FILE", PROJECT_DIR / "outputs" / "logs" / "tool_execution.jsonl"),
        )

    def validate(self) -> None:
        if self.max_tool_rounds < 1 or self.max_tool_rounds > 10:
            raise ValueError("MAX_TOOL_ROUNDS must be between 1 and 10")
        if self.model_timeout_seconds <= 0:
            raise ValueError("OLLAMA_TIMEOUT_SECONDS must be greater than zero")
        if self.knowledge_backend not in {"day07", "mock"}:
            raise ValueError("KNOWLEDGE_BACKEND must be 'day07' or 'mock'")


def actor_from_environment() -> ActorContext:
    return ActorContext(
        actor_id=os.getenv("APP_ACTOR_ID", "local-demo-user"),
        can_create_service_request=_bool("ALLOW_SERVICE_REQUEST_CREATE", False),
    )

