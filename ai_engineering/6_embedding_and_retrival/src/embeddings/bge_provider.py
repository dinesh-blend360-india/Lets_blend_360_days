"""Local Sentence Transformers provider for BAAI/bge-small-en-v1.5."""

from __future__ import annotations
from typing import Sequence
import numpy as np
from src.config import EmbeddingConfig

class BGEProvider:
    def __init__(self, config: EmbeddingConfig | None = None, *, model: object | None = None) -> None:
        self.config = config or EmbeddingConfig.from_environment()
        self.model_id = self.config.model_id
        if model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("Install sentence-transformers before loading the local BGE provider") from exc
            model = SentenceTransformer(self.model_id, device=self.config.device)
        self.model = model
        self.max_seq_length = int(getattr(model, "max_seq_length", 0) or 0)
        if self.max_seq_length <= 0:
            self.max_seq_length = int(getattr(getattr(model, "tokenizer", None), "model_max_length", 0) or 0)
        if self.max_seq_length <= 0 or self.max_seq_length > 1_000_000:
            self.max_seq_length = 512
        self.dimension = self._discover_dimension()

    def _discover_dimension(self) -> int:
        dimension = getattr(self.model, "get_sentence_embedding_dimension", lambda: None)()
        if dimension:
            return int(dimension)
        return int(self.embed_documents(["dimension probe"]).shape[1])

    def token_lengths(self, texts: Sequence[str]) -> list[int]:
        tokenizer = getattr(self.model, "tokenizer", None)
        if tokenizer is None:
            return [0 for _ in texts]
        encoded = tokenizer(list(texts), add_special_tokens=True, truncation=False)
        return [len(ids) for ids in encoded["input_ids"]]

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        values = self.model.encode(list(texts), batch_size=self.config.batch_size,
                                   normalize_embeddings=False, convert_to_numpy=True, show_progress_bar=False)
        vectors = np.asarray(values, dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {vectors.shape}")
        if not np.isfinite(vectors).all():
            raise ValueError("Embedding output contains non-finite values")
        if self.config.normalize:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError("Embedding output contains a zero vector")
            vectors = vectors / norms
        return vectors

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts)

    def embed_query(self, text: str) -> np.ndarray:
        if not text.strip():
            raise ValueError("Query cannot be empty")
        value = self.config.query_instruction + text if self.config.use_query_instruction else text
        return self._encode([value])[0]
