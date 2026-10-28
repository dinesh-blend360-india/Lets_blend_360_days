"""Optional live Ollama baseline using the same golden cases and checks."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_baseline import (
    ActorContext, AppConfig, ControlledAssistant, ExecutionLogger, KnowledgeLookup,
    ServiceRequestStore, ToolRegistry, checks, load_cases, ROOT,
)


def run_live_case(case: dict[str, Any], *, model_name: str, timeout: float, model_client: Any | None = None) -> dict[str, Any]:
    with TemporaryDirectory() as directory:
        base = Path(directory)
        config = replace(
            AppConfig.from_environment(), ollama_model=model_name,
            model_timeout_seconds=timeout, knowledge_backend="mock", max_tool_rounds=4,
            actions_dir=base / "actions", log_file=base / "tools.jsonl",
        )
        registry = ToolRegistry(KnowledgeLookup(config), ServiceRequestStore(config.actions_dir), ExecutionLogger(config.log_file))
        assistant = ControlledAssistant(config, model=model_client, registry=registry)
        scenario = case["scenario"]
        actor = ActorContext("live-eval-demo", scenario != "action_denied")
        started = perf_counter()
        result = assistant.handle(
            case["input"], actor=actor,
            confirmation_handler=lambda _: scenario == "action_confirmed",
        )
        duration_ms = round((perf_counter() - started) * 1000, 1)
        persisted_count = len(list(config.actions_dir.glob("SR-*.json")))
        return {
            "id": case["id"], "category": case["category"], "risk": case["risk"],
            "mode": "LIVE_OLLAMA", "model": model_name, "timeout_seconds": timeout,
            "input": case["input"], "expected": case["expected"],
            "assistant_output": result["final_response"], "assistant_ok": result["ok"],
            "tool_activity": result["tool_activity"], "persisted_actions": persisted_count,
            "checks": checks(case, result, persisted_count), "duration_ms": duration_ms,
            "judge": {"verdict": "NOT_RUN", "reason": "Blind human labels and judge calibration are separate"},
        }


def run_live(model_name: str, *, timeout: float = 45, ids: set[str] | None = None, output: Path | None = None) -> list[dict[str, Any]]:
    selected = [case for case in load_cases() if ids is None or case["id"] in ids]
    if ids and len(selected) != len(ids):
        raise ValueError("One or more requested case IDs were not found")
    rows = [run_live_case(case, model_name=model_name, timeout=timeout) for case in selected]
    destination = output or ROOT / "outputs" / "live_results.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Installed Ollama model name")
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--case", action="append", help="Repeat for selected case IDs; omit for all cases")
    args = parser.parse_args()
    results = run_live(args.model, timeout=args.timeout, ids=set(args.case) if args.case else None)
    print(f"Wrote {len(results)} live case results")
