"""Read-only adapter that captures each real Day 07 RAG stage."""

from __future__ import annotations

import importlib
import sys
import time
from typing import Any

from .config import EvaluationConfig


class Day07Adapter:
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self._modules: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._modules is not None:
            return self._modules
        project = str(self.config.day07_project_dir)
        if project not in sys.path:
            sys.path.insert(0, project)
        self._modules = {
            "retrieval": importlib.import_module("rag.day06_adapter"),
            "context": importlib.import_module("rag.context_builder"),
            "generation": importlib.import_module("rag.answer_generator"),
            "citations": importlib.import_module("rag.citation_validator"),
        }
        # Day 06 and Day 08 both use the top-level package name ``src``.
        # Day 07 normally imports Day 06 as ``src.retrieval.search``. Because
        # this evaluator itself is running as ``src``, load Day 06 in a short
        # isolated import window and return the module object to Day 07.
        self._modules["retrieval"]._load_day06_search_module = self._load_day06_search_module_isolated
        return self._modules

    def _load_day06_search_module_isolated(self) -> Any:
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

    def inspect(self) -> dict[str, Any]:
        modules = self._load()
        return modules["retrieval"].inspect_index(self.config.day06_index_dir)

    def run(self, question: str) -> dict[str, Any]:
        started = time.perf_counter()
        record: dict[str, Any] = {
            "question": question, "retrieved_chunks": [], "context": None,
            "generated_answer": None, "insufficient_evidence": None,
            "generated_citation_ids": [], "validated_citations": [],
            "final_response": None, "errors": [], "warnings": [],
        }
        try:
            modules = self._load()
            retrieved = modules["retrieval"].search(
                question, index_dir=self.config.day06_index_dir, top_k=self.config.top_k
            )
            record["retrieved_chunks"] = retrieved
        except Exception as exc:
            record["errors"].append(_error("RUNTIME_OR_CONFIGURATION", exc))
            return _finish(record, started)

        try:
            context = modules["context"].build_context(
                question, retrieved, max_context_chars=self.config.max_context_chars
            )
            record["context"] = context.as_dict()
        except Exception as exc:
            record["errors"].append(_error("CONTEXT_CONSTRUCTION", exc))
            return _finish(record, started)

        if not context.evidence:
            insufficient = modules["generation"].INSUFFICIENT_ANSWER
            record.update({
                "generated_answer": insufficient, "insufficient_evidence": True,
                "final_response": {"answer": insufficient, "insufficient_evidence": True, "citations": [], "sources": []},
            })
            return _finish(record, started)

        try:
            generated = modules["generation"].generate_answer(
                question, context.formatted_context, [item.chunk_id for item in context.evidence]
            )
            generated_dict = generated.as_dict() if hasattr(generated, "as_dict") else dict(generated)
            record["generated_answer"] = generated_dict.get("answer")
            record["insufficient_evidence"] = generated_dict.get("insufficient_evidence")
            record["generated_citation_ids"] = generated_dict.get("citations", [])
        except Exception as exc:
            stage = "RUNTIME_OR_CONFIGURATION" if type(exc).__name__ in {"ModelUnavailableError", "ModuleNotFoundError", "ImportError"} else "GENERATION_GROUNDING"
            record["errors"].append(_error(stage, exc))
            return _finish(record, started)

        try:
            final = modules["citations"].validate_citations(
                generated, context.evidence, retrieved_count=len(retrieved),
                retrieval_results=retrieved, include_debug=True,
            )
            record["final_response"] = final
            record["validated_citations"] = final.get("citations", [])
        except Exception as exc:
            record["errors"].append(_error("CITATION_MAPPING", exc))
        return _finish(record, started)


def _error(stage: str, exc: Exception) -> dict[str, str]:
    return {"stage": stage, "type": type(exc).__name__, "message": str(exc)}


def _finish(record: dict[str, Any], started: float) -> dict[str, Any]:
    record["runtime_seconds"] = round(time.perf_counter() - started, 6)
    return record

