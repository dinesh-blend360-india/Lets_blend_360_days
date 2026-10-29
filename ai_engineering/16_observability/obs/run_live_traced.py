"""Run Day 15 cases against a live Ollama model, with tracing.

The scripted baseline cannot show a prompt fix working, because Day 15's
`ScenarioModel` returns fixture replies and never reads the system prompt. A
prompt change is only observable against a real model, so the before/after
evidence for the Day 16 fix is produced here.

Same cases, same checks, same mock knowledge backend as Day 15. The only thing
that differs between the before and after runs is --prompt-version.

    python -m obs.run_live_traced --model llama3.2:3b --prompt-version v1 \
        --case D15-03 --out outputs/live_before.jsonl
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Any

from .faults import FAULTS, FaultConfig
from .instrumented import DEFAULT_PROMPT_VERSION, PROMPT_VERSIONS, build_traced_assistant, traced_handle
from .tracing import Tracer, render_tree


PROJECT_DIR = Path(__file__).resolve().parents[1]
AI_ENGINEERING_DIR = PROJECT_DIR.parent
DAY10_DIR = AI_ENGINEERING_DIR / "10_tool_calling"
DAY15_DIR = AI_ENGINEERING_DIR / "15_evaluations"
TRACE_DIR = PROJECT_DIR / "outputs" / "traces"

for path in (DAY10_DIR, DAY15_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src.config import ActorContext, AppConfig  # noqa: E402
from src.execution_logger import ExecutionLogger  # noqa: E402
from src.knowledge_lookup import KnowledgeLookup  # noqa: E402
from src.model_client import OllamaModelClient  # noqa: E402
from src.service_request import ServiceRequestStore  # noqa: E402
from src.tool_registry import ToolRegistry  # noqa: E402

import run_baseline as day15  # noqa: E402


def run_live_case(
    case: dict[str, Any],
    *,
    model_name: str,
    timeout: float = 45.0,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    faults: FaultConfig | None = None,
    trace_dir: Path | None = TRACE_DIR,
) -> tuple[dict[str, Any], Tracer]:
    faults = faults or FaultConfig()
    with TemporaryDirectory() as directory:
        base = Path(directory)
        config = replace(
            AppConfig.from_environment(),
            ollama_model=model_name,
            model_timeout_seconds=timeout,
            knowledge_backend="mock",
            max_tool_rounds=4,
            actions_dir=base / "actions",
            log_file=base / "tools.jsonl",
        )
        tracer = Tracer(
            trace_dir,
            base_metadata={
                "model": model_name,
                "prompt_version": prompt_version,
                "knowledge_backend": config.knowledge_backend,
                "mode": "LIVE_OLLAMA",
                **faults.as_dict(),
            },
        )
        scenario = case["scenario"]
        registry = ToolRegistry(
            KnowledgeLookup(config), ServiceRequestStore(config.actions_dir), ExecutionLogger(config.log_file)
        )
        assistant = build_traced_assistant(
            model=OllamaModelClient(config),
            tracer=tracer,
            config=config,
            faults=faults,
            prompt_version=prompt_version,
            registry=registry,
        )
        actor = ActorContext("day16-live", scenario != "action_denied")
        result = traced_handle(
            assistant,
            case["input"],
            tracer=tracer,
            actor=actor,
            confirmation_handler=lambda _: scenario == "action_confirmed",
            prompt_version=prompt_version,
            case_id=case["id"],
        )
        persisted = len(list(config.actions_dir.glob("SR-*.json")))
        tracer.flush()
        row = {
            "id": case["id"],
            "category": case["category"],
            "risk": case["risk"],
            "mode": "LIVE_OLLAMA",
            "model": model_name,
            "prompt_version": prompt_version,
            "fault": faults.name,
            "input": case["input"],
            "expected": case["expected"],
            "assistant_output": result["final_response"],
            "assistant_ok": result["ok"],
            "tool_activity": result["tool_activity"],
            "persisted_actions": persisted,
            "checks": day15.checks(case, result, persisted),
            "trace": tracer.summary(),
        }
        return row, tracer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="Installed Ollama model name")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--case", action="append", help="Case ID; repeatable. Omit for all cases")
    parser.add_argument("--prompt-version", choices=sorted(PROMPT_VERSIONS), default=DEFAULT_PROMPT_VERSION)
    parser.add_argument("--fault", choices=FAULTS)
    parser.add_argument("--out", type=Path, help="Write result rows to this JSONL file")
    parser.add_argument("--show-trace", action="store_true")
    args = parser.parse_args()

    faults = FaultConfig(FaultConfig.parse(args.fault))
    cases = day15.load_cases()
    if args.case:
        wanted = {item.upper() for item in args.case}
        cases = [case for case in cases if case["id"].upper() in wanted]
        missing = wanted - {case["id"].upper() for case in cases}
        if missing:
            parser.error(f"Unknown case ID(s): {', '.join(sorted(missing))}")

    rows: list[dict[str, Any]] = []
    for case in cases:
        row, tracer = run_live_case(
            case,
            model_name=args.model,
            timeout=args.timeout,
            prompt_version=args.prompt_version,
            faults=faults,
        )
        rows.append(row)
        failed = [name for name, passed in row["checks"].items() if not passed]
        print(
            f"{row['id']:<8} prompt={row['prompt_version']} "
            f"total={row['trace']['total_ms']}ms steps={row['trace']['step_count']} "
            f"tools={[item['tool_name'] for item in row['tool_activity']]} "
            f"failed_checks={failed or 'none'}",
            flush=True,
        )
        if args.show_trace:
            print(render_tree(tracer.records()))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows) + "\n", encoding="utf-8"
        )
        print(f"\nWrote {len(rows)} row(s) to {args.out}")
    failures = [(row["id"], name) for row in rows for name, ok in row["checks"].items() if not ok]
    print(f"{len(rows)} live case(s); {len(failures)} deterministic check failures")


if __name__ == "__main__":
    main()
