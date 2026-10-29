"""Regenerate the committed trace evidence under evidence/traces/.

Reviewers cannot open someone else's LangSmith project, so the traces behind
each diagnosis are exported into the repository. Each file is one trace in the
fallback record shape, with a .txt tree beside it for reading by eye.

    python -m obs.make_evidence              # scripted scenarios only
    python -m obs.make_evidence --model llama3.2:3b   # also the live D15-03 trace
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .faults import FaultConfig
from .run_traced import F16_06_MESSAGE, run_case, run_message
from .tracing import Tracer, render_tree


PROJECT_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = PROJECT_DIR / "evidence" / "traces"


def _save(name: str, tracer: Tracer, note: str) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    records = tracer.records()
    (EVIDENCE_DIR / f"{name}.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, default=str) for record in records) + "\n",
        encoding="utf-8",
    )
    summary = tracer.summary()
    (EVIDENCE_DIR / f"{name}.txt").write_text(
        f"{note}\n\n{render_tree(records)}\n\nsummary: {json.dumps(summary, indent=2)}\n",
        encoding="utf-8",
    )
    print(f"  wrote {name}.jsonl / .txt  ({summary['step_count']} steps, {summary['total_ms']} ms)")


def _case(case_id: str) -> dict[str, Any]:
    from .run_traced import day15

    return next(case for case in day15.load_cases() if case["id"] == case_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", help="Also capture the live D15-03 trace with this Ollama model")
    args = parser.parse_args()

    print("Scripted scenarios:")

    # F16-01 slow_tool: the latency shape.
    _, tracer = run_case(_case("D15-01"), faults=FaultConfig("slow_tool"), trace_dir=None)
    _save("F16-01_slow_tool_D15-01", tracer, "F16-01 slow_tool: the tool run dominates total time.")

    # F16-02 flaky_tool, before and after the retry fix.
    _, tracer = run_case(_case("D15-01"), faults=FaultConfig("flaky_tool"), trace_dir=None, retry_attempts=0)
    _save(
        "F16-02_flaky_tool_D15-01_before_retry0",
        tracer,
        "F16-02 before the fix: one errored tool run, no retry, source_citation fails.",
    )
    _, tracer = run_case(_case("D15-01"), faults=FaultConfig("flaky_tool"), trace_dir=None, retry_attempts=2)
    _save(
        "F16-02_flaky_tool_D15-01_after_retry2",
        tracer,
        "F16-02 after the fix: three tool runs (two errored, then success); all checks pass.",
    )

    # The other failing shapes under flaky_tool, so the committed evidence
    # covers more than one case: D15-02 makes two lookups, D15-16 is the
    # Hinglish variant. Both fail source_citation before the fix.
    for case_id, shape in (("D15-02", "two_lookups"), ("D15-16", "hinglish_variant")):
        _, tracer = run_case(_case(case_id), faults=FaultConfig("flaky_tool"), trace_dir=None, retry_attempts=0)
        _save(
            f"F16-02_flaky_tool_{case_id}_before_retry0",
            tracer,
            f"F16-02 before the fix on {case_id} ({shape}): transient tool failure, source_citation fails.",
        )

    # F16-03 mcp_error: the error surfaces on the tool run.
    _, tracer = run_case(_case("D15-01"), faults=FaultConfig("mcp_error"), trace_dir=None)
    _save("F16-03_mcp_error_D15-01", tracer, "F16-03 mcp_error: transport error on the tool run.")

    # F16-04 bad_retrieval: no error anywhere, but retrieval returned nothing.
    _, tracer = run_case(_case("D15-01"), faults=FaultConfig("bad_retrieval"), trace_dir=None)
    _save(
        "F16-04_bad_retrieval_D15-01",
        tracer,
        "F16-04 bad_retrieval: no errored step; the retriever run returned 0 documents.",
    )

    # F16-05 prompt_bloat: token count on the llm runs.
    _, tracer = run_case(_case("D15-01"), faults=FaultConfig("prompt_bloat"), trace_dir=None)
    _save("F16-05_prompt_bloat_D15-01", tracer, "F16-05 prompt_bloat: approx_input_tokens on each llm run rises.")

    # F16-06 privacy: masking proven in the exported trace.
    _, tracer = run_message(F16_06_MESSAGE, trace_dir=None)
    _save(
        "F16-06_masking_personal_data",
        tracer,
        "F16-06 data case: employee ID and email appear only as placeholders in every run.",
    )

    if args.model:
        print(f"Live scenario with {args.model}:")
        from .run_live_traced import run_live_case

        # The note is written from the observed run, not asserted in advance:
        # this model picks a different wrong tool on different runs, so a
        # hardcoded description would go stale the next time this is generated.
        for version, label in (("v1", "shipped_prompt"), ("v2", "rejected_fix")):
            row, tracer = run_live_case(
                _case("D15-03"), model_name=args.model, prompt_version=version, trace_dir=None
            )
            tools = [item["tool_name"] for item in row["tool_activity"]]
            failed = sorted(name for name, ok in row["checks"].items() if not ok)
            note = (
                f"T16-01 / D15-03 live on {args.model}, prompt {version} ({label}).\n"
                f"Expected no tool call. Tools actually called: {tools or 'none'}.\n"
                f"Failed Day 15 checks: {failed or 'none'}.\n"
                f"Final answer: {row['assistant_output'][:200]!r}\n"
                "Note: this model's wrong choice varies between runs; the constant is that "
                "llm_call (1) requests some tool for a question that needs none."
            )
            _save(f"T16-01_D15-03_live_{version}_{label}", tracer, note)


if __name__ == "__main__":
    main()
