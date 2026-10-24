"""Numerically safe cosine-similarity helpers."""

from __future__ import annotations
import numpy as np

def cosine_similarity(query: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    query, vectors = np.asarray(query, dtype=np.float32), np.asarray(vectors, dtype=np.float32)
    if query.ndim != 1 or vectors.ndim != 2 or vectors.shape[1] != query.shape[0]:
        raise ValueError(f"Incompatible vector dimensions: query {query.shape}, vectors {vectors.shape}")
    if not np.isfinite(query).all() or not np.isfinite(vectors).all():
        raise ValueError("Vectors must contain only finite values")
    query_norm, vector_norms = np.linalg.norm(query), np.linalg.norm(vectors, axis=1)
    if query_norm == 0 or np.any(vector_norms == 0):
        raise ValueError("Cosine similarity is undefined for zero vectors")
    return (vectors @ query) / (vector_norms * query_norm)

def top_k(query: np.ndarray, vectors: np.ndarray, k: int) -> list[tuple[int, float]]:
    if k <= 0:
        raise ValueError("Top-K must be greater than zero")
    scores = cosine_similarity(query, vectors)
    order = np.argsort(-scores, kind="stable")[:k]
    return [(int(index), float(scores[index])) for index in order]
