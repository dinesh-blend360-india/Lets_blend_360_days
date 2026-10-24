"""Deterministic retrieval metrics for cases with verified relevance labels."""

from __future__ import annotations

from statistics import mean
from typing import Iterable


def recall_at_k(retrieved_ids: Iterable[str], relevant_ids: Iterable[str], k: int) -> float | None:
    relevant = set(relevant_ids)
    if not relevant:
        return None
    if k <= 0:
        raise ValueError("k must be greater than zero")
    return len(relevant.intersection(list(retrieved_ids)[:k])) / len(relevant)


def reciprocal_rank(retrieved_ids: Iterable[str], relevant_ids: Iterable[str]) -> float | None:
    relevant = set(relevant_ids)
    if not relevant:
        return None
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant:
            return 1.0 / rank
    return 0.0


def retrieval_metrics(retrieved_ids: list[str], relevant_ids: list[str]) -> dict[str, float | bool | None]:
    return {
        "hit_at_configured_k": bool(set(retrieved_ids).intersection(relevant_ids)) if relevant_ids else None,
        "recall_at_1": recall_at_k(retrieved_ids, relevant_ids, 1),
        "recall_at_3": recall_at_k(retrieved_ids, relevant_ids, 3),
        "recall_at_5": recall_at_k(retrieved_ids, relevant_ids, 5),
        "reciprocal_rank": reciprocal_rank(retrieved_ids, relevant_ids),
    }


def mean_reciprocal_rank(records: Iterable[dict]) -> float | None:
    values = [record.get("retrieval_metrics", {}).get("reciprocal_rank") for record in records]
    valid = [float(value) for value in values if value is not None]
    return mean(valid) if valid else None

