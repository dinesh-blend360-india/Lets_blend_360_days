"""Strictly read-only knowledge lookup using Day 07 or an explicit mock backend."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any, Callable

from .config import AppConfig


Retriever = Callable[..., list[dict[str, Any]]]


class KnowledgeLookup:
    def __init__(self, config: AppConfig, retriever: Retriever | None = None):
        self.config = config
        self.retriever = retriever
        self._day07_module: Any | None = None

    def lookup(self, query: str, *, category: str | None, top_k: int) -> dict[str, Any]:
        if self.retriever is not None:
            raw = self.retriever(query, index_dir=self.config.day06_index_dir, top_k=top_k)
            backend = "injected"
        elif self.config.knowledge_backend == "mock":
            raw = self._mock_search(query, top_k)
            backend = "mock"
        else:
            raw = self._day07_search(query, top_k)
            backend = "day07"
        normalized = [self._normalize(item) for item in raw]
        if category:
            marker = "expense" if category == "expense_policy" else "travel"
            normalized = [item for item in normalized if marker in str(item["heading_path"]).casefold()]
        normalized = normalized[:top_k]
        return {
            "ok": True,
            "tool_name": "lookup_internal_knowledge",
            "backend": backend,
            "no_results": not normalized,
            "results": normalized,
        }

    def _load_day07(self) -> Any:
        if self._day07_module is not None:
            return self._day07_module
        project = str(self.config.day07_project_dir)
        if project not in sys.path:
            sys.path.insert(0, project)
        module = importlib.import_module("rag.day06_adapter")
        module._load_day06_search_module = self._load_day06_isolated
        self._day07_module = module
        return module

    def _load_day06_isolated(self) -> Any:
        day06_dir = self.config.day06_index_dir.parents[2]
        saved = {name: module for name, module in sys.modules.items() if name == "src" or name.startswith("src.")}
        original_path = list(sys.path)
        for name in saved:
            sys.modules.pop(name, None)
        sys.path.insert(0, str(day06_dir))
        try:
            module = importlib.import_module("src.retrieval.search")
        finally:
            for name in list(sys.modules):
                if name == "src" or name.startswith("src."):
                    sys.modules.pop(name, None)
            sys.modules.update(saved)
            sys.path[:] = original_path
        return module

    def _day07_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        return self._load_day07().search(query, index_dir=self.config.day06_index_dir, top_k=top_k)

    def _mock_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        records = json.loads(self.config.mock_knowledge_file.read_text(encoding="utf-8"))
        terms = {part.casefold() for part in query.split() if len(part) > 2}
        ranked = []
        for item in records:
            haystack = f"{item.get('text', '')} {item.get('metadata', {}).get('heading_path', '')}".casefold()
            score = sum(term in haystack for term in terms) / max(len(terms), 1)
            if score:
                ranked.append({**item, "similarity": score})
        ranked.sort(key=lambda item: item["similarity"], reverse=True)
        return [{**item, "rank": rank} for rank, item in enumerate(ranked[:top_k], start=1)]

    @staticmethod
    def _normalize(item: dict[str, Any]) -> dict[str, Any]:
        metadata = item.get("metadata") or {}
        page = metadata.get("page")
        if page is None:
            start, end = metadata.get("page_start"), metadata.get("page_end")
            page = f"{start}-{end}" if start is not None and end is not None and start != end else start if start is not None else end
        return {
            "chunk_id": str(item.get("chunk_id") or metadata.get("chunk_id") or ""),
            "source": metadata.get("source"),
            "text": item.get("text", ""),
            "heading_path": metadata.get("heading_path"),
            "page": page,
            "score": float(item.get("similarity", 0.0)),
            "rank": int(item.get("rank", 0)),
        }

