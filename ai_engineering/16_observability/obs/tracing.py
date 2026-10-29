"""A minimal nested-run tracer with a local file backend and optional LangSmith.

One request produces one trace: a tree of runs. The root run is the whole
request; retrieval, each LLM call and each tool call are child runs carrying
their own inputs, outputs, timing, error and metadata.

The local backend is the default and needs no account. It writes the record
shape the Day 16 brief specifies as the LangSmith fallback: one JSON object per
step with run_id, parent_run_id, trace_id, name, run_type, start and end time,
inputs, outputs, error and metadata.

LangSmith is used instead when LANGSMITH_TRACING=true and the langsmith package
imports. Every payload is masked before it reaches either backend.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Iterator
from uuid import uuid4

from .masking import mask


RunType = str  # "chain" | "llm" | "retriever" | "tool"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Run:
    run_id: str
    trace_id: str
    parent_run_id: str | None
    name: str
    run_type: RunType
    start_time: str
    inputs: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    end_time: str | None = None
    outputs: Any = None
    error: str | None = None
    duration_ms: float | None = None

    def as_record(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "parent_run_id": self.parent_run_id,
            "name": self.name,
            "run_type": self.run_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "metadata": self.metadata,
        }


class Tracer:
    """Collects nested runs for one process and writes them per trace.

    `trace_dir` receives one JSONL file per trace, named by trace_id. Masking is
    applied in `start_run`/`end_run`, so nothing unmasked is ever held on a Run.
    """

    def __init__(
        self,
        trace_dir: Path | None = None,
        *,
        base_metadata: dict[str, Any] | None = None,
        use_langsmith: bool | None = None,
    ):
        self.trace_dir = Path(trace_dir) if trace_dir else None
        self.base_metadata = dict(base_metadata or {})
        self.runs: list[Run] = []
        self._stack: list[Run] = []
        self._client = None
        self.backend = "local"
        if use_langsmith is None:
            use_langsmith = os.getenv("LANGSMITH_TRACING", "").strip().lower() == "true"
        if use_langsmith:
            self._client = self._make_langsmith_client()
            if self._client is not None:
                self.backend = "langsmith+local"

    @staticmethod
    def _make_langsmith_client():
        """Return a LangSmith client, or None if unavailable. Never fatal:
        losing tracing must not take the assistant down with it."""
        if not os.getenv("LANGSMITH_API_KEY"):
            return None
        try:
            from langsmith import Client

            return Client()
        except Exception:
            return None

    # ── Run lifecycle ──────────────────────────────────────────────────
    @property
    def current(self) -> Run | None:
        return self._stack[-1] if self._stack else None

    def start_run(self, name: str, run_type: RunType, inputs: Any, **metadata: Any) -> Run:
        parent = self.current
        run = Run(
            run_id=uuid4().hex,
            trace_id=parent.trace_id if parent else uuid4().hex,
            parent_run_id=parent.run_id if parent else None,
            name=name,
            run_type=run_type,
            start_time=_now(),
            inputs=mask(inputs),
            metadata={**self.base_metadata, **mask(metadata)},
        )
        run._monotonic = time.perf_counter()  # type: ignore[attr-defined]
        self.runs.append(run)
        self._stack.append(run)
        return run

    def end_run(self, run: Run, outputs: Any = None, error: BaseException | str | None = None) -> None:
        run.end_time = _now()
        started = getattr(run, "_monotonic", None)
        run.duration_ms = round((time.perf_counter() - started) * 1000, 2) if started else None
        run.outputs = mask(outputs)
        if error is not None:
            run.error = mask(error if isinstance(error, str) else f"{type(error).__name__}: {error}")
        if self._stack and self._stack[-1] is run:
            self._stack.pop()

    @contextmanager
    def run(self, name: str, run_type: RunType, inputs: Any, **metadata: Any) -> Iterator[Run]:
        """Trace a block. An exception is recorded on the run and re-raised, so
        a fault shows up as an errored step instead of vanishing."""
        run = self.start_run(name, run_type, inputs, **metadata)
        try:
            yield run
        except BaseException as exc:
            self.end_run(run, outputs=None, error=exc)
            raise
        else:
            if run.end_time is None:
                self.end_run(run, outputs=run.outputs)

    # ── Export ─────────────────────────────────────────────────────────
    def records(self) -> list[dict[str, Any]]:
        return [run.as_record() for run in self.runs]

    def root(self) -> Run | None:
        return next((run for run in self.runs if run.parent_run_id is None), None)

    def total_ms(self) -> float:
        root = self.root()
        return root.duration_ms or 0.0 if root else 0.0

    def slowest(self, exclude_root: bool = True) -> Run | None:
        pool = [r for r in self.runs if not (exclude_root and r.parent_run_id is None)]
        return max(pool, key=lambda r: r.duration_ms or 0.0, default=None)

    def errors(self) -> list[Run]:
        return [run for run in self.runs if run.error]

    def flush(self) -> Path | None:
        """Write this trace to <trace_dir>/<trace_id>.jsonl and return the path."""
        if not self.trace_dir or not self.runs:
            return None
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        trace_id = self.runs[0].trace_id
        path = self.trace_dir / f"{trace_id}.jsonl"
        path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False, default=str) for record in self.records()) + "\n",
            encoding="utf-8",
        )
        self._post_to_langsmith()
        return path

    def _post_to_langsmith(self) -> None:
        """Best-effort upload. A tracing failure is never allowed to fail a run."""
        if self._client is None:
            return
        project = os.getenv("LANGSMITH_PROJECT", "day16-observability")
        for record in self.records():
            try:
                self._client.create_run(
                    id=record["run_id"],
                    trace_id=record["trace_id"],
                    parent_run_id=record["parent_run_id"],
                    name=record["name"],
                    run_type=record["run_type"],
                    inputs=record["inputs"] if isinstance(record["inputs"], dict) else {"value": record["inputs"]},
                    outputs=record["outputs"] if isinstance(record["outputs"], dict) else {"value": record["outputs"]},
                    error=record["error"],
                    extra={"metadata": record["metadata"]},
                    project_name=project,
                )
            except Exception:
                return

    def summary(self) -> dict[str, Any]:
        """The few numbers a diagnosis actually quotes."""
        slowest = self.slowest()
        by_type: dict[str, float] = {}
        for run in self.runs:
            if run.parent_run_id is None:
                continue
            by_type[run.run_type] = round(by_type.get(run.run_type, 0.0) + (run.duration_ms or 0.0), 2)
        return {
            "trace_id": self.runs[0].trace_id if self.runs else None,
            "backend": self.backend,
            "step_count": len(self.runs),
            "total_ms": self.total_ms(),
            "ms_by_run_type": by_type,
            "slowest_step": {"name": slowest.name, "ms": slowest.duration_ms} if slowest else None,
            "error_steps": [{"name": run.name, "error": run.error} for run in self.errors()],
        }


def render_tree(records: list[dict[str, Any]]) -> str:
    """Render a saved trace as an indented tree — the view used when reading a
    trace by eye, matching the table layout in the Day 16 scenario document."""
    children: dict[str | None, list[dict[str, Any]]] = {}
    for record in records:
        children.setdefault(record["parent_run_id"], []).append(record)
    lines: list[str] = []

    def walk(parent: str | None, depth: int) -> None:
        for record in children.get(parent, []):
            ms = record.get("duration_ms")
            marker = "  ERROR" if record.get("error") else ""
            lines.append(f"{'  ' * depth}{record['name']:<28} {record['run_type']:<10} {ms:>9} ms{marker}")
            walk(record["run_id"], depth + 1)

    walk(None, 0)
    return "\n".join(lines)
