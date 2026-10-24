"""Configuration loaded from environment variables and repository-relative defaults."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
AI_ENGINEERING_DIR = PROJECT_DIR.parent


def _path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    path = Path(value) if value else default
    return path if path.is_absolute() else (PROJECT_DIR / path).resolve()


@dataclass(frozen=True)
class EvaluationConfig:
    day07_project_dir: Path
    day06_index_dir: Path
    cases_file: Path
    output_dir: Path
    top_k: int = 5
    max_context_chars: int = 6000

    @classmethod
    def from_environment(cls) -> "EvaluationConfig":
        return cls(
            day07_project_dir=_path("DAY07_PROJECT_DIR", AI_ENGINEERING_DIR / "7_rag"),
            day06_index_dir=_path(
                "DAY06_INDEX_DIR",
                AI_ENGINEERING_DIR / "06_embedding_and_retrieval" / "outputs" / "embeddings" / "employee_policy_md_structure",
            ),
            cases_file=_path("DAY08_CASES_FILE", PROJECT_DIR / "test_inputs" / "day08_common_cases.json"),
            output_dir=_path("DAY08_OUTPUT_DIR", PROJECT_DIR / "outputs"),
            top_k=int(os.getenv("DAY08_TOP_K", "5")),
            max_context_chars=int(os.getenv("DAY08_MAX_CONTEXT_CHARS", "6000")),
        )

    def validate(self) -> None:
        if self.top_k <= 0:
            raise ValueError("DAY08_TOP_K must be greater than zero")
        if self.max_context_chars <= 0:
            raise ValueError("DAY08_MAX_CONTEXT_CHARS must be greater than zero")
        if not self.day07_project_dir.is_dir():
            raise FileNotFoundError(f"Day 07 project not found: {self.day07_project_dir}")
        if not self.cases_file.is_file():
            raise FileNotFoundError(f"Evaluation cases not found: {self.cases_file}")

    def as_dict(self) -> dict[str, Any]:
        return {key: str(value) if isinstance(value, Path) else value for key, value in asdict(self).items()}

