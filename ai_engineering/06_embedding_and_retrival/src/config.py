"""Shared configuration for the local embedding and retrieval workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os

DEFAULT_MODEL_ID = "BAAI/bge-small-en-v1.5"
DEFAULT_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class EmbeddingConfig:
    model_id: str = DEFAULT_MODEL_ID
    batch_size: int = 32
    normalize: bool = True
    use_query_instruction: bool = True
    query_instruction: str = DEFAULT_QUERY_INSTRUCTION
    device: str = "cpu"

    @classmethod
    def from_environment(cls) -> "EmbeddingConfig":
        return cls(
            model_id=os.getenv("EMBEDDING_MODEL_ID", DEFAULT_MODEL_ID),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
            normalize=_env_bool("EMBEDDING_NORMALIZE", True),
            use_query_instruction=_env_bool("EMBEDDING_USE_QUERY_INSTRUCTION", True),
            device=os.getenv("EMBEDDING_DEVICE", "cpu"),
        )

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
