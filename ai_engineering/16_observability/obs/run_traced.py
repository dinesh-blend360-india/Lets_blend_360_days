"""Run Day 15 cases through the traced assistant.

This reuses Day 15's own case list, scripted model and deterministic checks, so
a before/after comparison is the same suite with the same settings. The only
variables are the prompt version and the fault flag.

    python -m obs.run_traced --all --prompt-version v1 --out outputs/before.jsonl
    python -m obs.run_traced --case D15-03 --fault slow_tool
    python -m obs.run_traced --message "My employee ID is E1023 ..." --show-trace
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
from .instrumented import (
    DEFAULT_PROMPT_VERSION,
    DEFAULT_RETRY_ATTEMPTS,
    PROMPT_VERSIONS,
    build_traced_assistant,
    traced_handle,
)
from .tracing import Tracer, render_tree


PROJECT_DIR = Path(__file__).resolve().parents[1]
AI_ENGINEERING_DIR = PROJECT_DIR.parent
DAY10_DIR = AI_ENGINEERING_DIR / "10_tool_calling"
DAY15_DIR = AI_ENGINEERING_DIR / "15_evaluations"
TRACE_DIR = PROJECT_DIR / "outputs" / "traces"

for path in (DAY10_DIR, DAY15_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src.config import ActorContext, AppConfig  # noqa: E402  (Day 10)
from src.execution_logger import ExecutionLogger  # noqa: E402
from src.knowledge_lookup import KnowledgeLookup  # noqa: E402
from src.service_request import ServiceRequestStore  # noqa: E402
from src.tool_registry import ToolRegistry  # noqa: E402

import run_baseline as day15  # noqa: E402  (Day 15 suite: cases, model, checks)


# The data case from the scenario document: personal data in the message.
F16_06_MESSAGE = (
    "My employee ID is E1023 and my email is asha.rao@example.com. "
    "What is the expense claim deadline?"
)


def run_case(
    case: dict[str, Any],
    *,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    faults: FaultConfig | None = None,
    trace_dir: Path | None = TRACE_DIR,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> tuple[dict[str, Any], Tracer]:
    """Run one Day 15 case under tracing and apply Day 15's own checks."""
    faults = faults or FaultConfig()
    with TemporaryDirectory() as directory:
        base = Path(directory)
        config = replace(
            AppConfig.from_environment(),
            knowledge_backend="mock",
            actions_dir=base / "actions",
            log_file=base / "tools.jsonl",
        )
        tracer = Tracer(
            trace_dir,
            base_metadata={
                "model": config.ollama_model,
                "prompt_version": prompt_version,
                "knowledge_backend": config.knowledge_backend,
                "retry_attempts": retry_attempts,
                **faults.as_dict(),
            },
        )
        scenario = case["scenario"]
        registry = ToolRegistry(
            KnowledgeLookup(config), ServiceRequestStore(config.actions_dir), ExecutionLogger(config.log_file)
        )
        assistant = build_traced_assistant(
            model=day15.ScenarioModel(scenario),
            tracer=tracer,
            config=config,
            faults=faults,
            prompt_version=prompt_version,
            registry=registry,
            retry_attempts=retry_attempts,
        )
        actor = ActorContext("day16-traced", scenario != "action_denied")
        confirmed = scenario == "action_confirmed"
        result = traced_handle(
            assistant,
            case["input"],
            tracer=tracer,
            actor=actor,
            confirmation_handler=lambda _: confirmed,
            prompt_version=prompt_version,
            case_id=case["id"],
        )
        persisted = len(list(config.actions_dir.glob("SR-*.json")))
        tracer.flush()
        row = {
            "id": case["id"],
            "category": case["category"],
            "risk": case["risk"],
            "mode": "SCRIPTED_MOCK",
            "prompt_version": prompt_version,
            "fault": faults.name,
            "retry_attempts": retry_attempts,
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


def run_message(
    message: str,
    *,
    scenario: str = "lookup_expense",
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    faults: FaultConfig | None = None,
    trace_dir: Path | None = TRACE_DIR,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> tuple[dict[str, Any], Tracer]:
    """Run an arbitrary message (used for the F16-06 privacy case)."""
    case = {
        "id": "AD-HOC",
        "category": "ad_hoc",
        "risk": "low",
        "input": message,
        "expected": "Ad-hoc message; Day 15 checks do not apply.",
        "scenario": scenario,
    }
    row, tracer = run_case(
        case, prompt_version=prompt_version, faults=faults, trace_dir=trace_dir, retry_attempts=retry_attempts
    )
    row.pop("checks", None)
    return row, tracer


def _write(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--all", action="store_true", help="Run every Day 15 case")
    target.add_argument("--case", action="append", help="Run one Day 15 case ID; repeatable")
    target.add_argument("--message", help="Run one ad-hoc message")
    target.add_argument("--privacy-case", action="store_true", help="Run F16-06, the personal-data message")
    parser.add_argument("--prompt-version", choices=sorted(PROMPT_VERSIONS), default=DEFAULT_PROMPT_VERSION)
    parser.add_argument("--fault", choices=FAULTS, help="Switch on one deliberate fault (default: none)")
    parser.add_argument(
        "--retry", type=int, default=DEFAULT_RETRY_ATTEMPTS,
        help="Bounded retry attempts for transient tool failures (the Day 16 fix; 0 = original behaviour)",
    )
    parser.add_argument("--out", type=Path, help="Write result rows to this JSONL file")
    parser.add_argument("--show-trace", action="store_true", help="Print the trace tree for each run")
    parser.add_argument("--scenario", default="lookup_expense", help="Scripted scenario for --message")
    args = parser.parse_args()

    faults = FaultConfig(FaultConfig.parse(args.fault))
    rows: list[dict[str, Any]] = []
    tracers: list[Tracer] = []

    if args.message or args.privacy_case:
        message = F16_06_MESSAGE if args.privacy_case else args.message
        row, tracer = run_message(
            message, scenario=args.scenario, prompt_version=args.prompt_version,
            faults=faults, retry_attempts=args.retry,
        )
        rows.append(row)
        tracers.append(tracer)
    else:
        cases = day15.load_cases()
        if args.case:
            wanted = {item.upper() for item in args.case}
            cases = [case for case in cases if case["id"].upper() in wanted]
            missing = wanted - {case["id"].upper() for case in cases}
            if missing:
                parser.error(f"Unknown case ID(s): {', '.join(sorted(missing))}")
        for case in cases:
            row, tracer = run_case(
                case, prompt_version=args.prompt_version, faults=faults, retry_attempts=args.retry
            )
            rows.append(row)
            tracers.append(tracer)

    for row, tracer in zip(rows, tracers):
        summary = row["trace"]
        failed = [name for name, passed in row.get("checks", {}).items() if not passed]
        print(
            f"{row['id']:<8} prompt={row['prompt_version']} fault={row['fault']} retry={row['retry_attempts']} "
            f"steps={summary['step_count']} total={summary['total_ms']}ms "
            f"errors={len(summary['error_steps'])} failed_checks={failed or 'none'}"
        )
        if args.show_trace:
            print(render_tree(tracer.records()))
            print(f"  trace file: {TRACE_DIR / (summary['trace_id'] + '.jsonl')}")

    if args.out:
        _write(rows, args.out)
        print(f"\nWrote {len(rows)} row(s) to {args.out}")


if __name__ == "__main__":
    main()
