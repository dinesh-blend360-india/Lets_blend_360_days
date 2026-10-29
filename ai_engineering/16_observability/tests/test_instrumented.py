"""Instrumentation behaviour against the real Day 10 assistant.

These use Day 15's scripted model and Day 10's mock knowledge backend, so they
need no network and no Ollama.
"""

import pytest

from obs.faults import FaultConfig
from obs.instrumented import PROMPT_V1, PROMPT_V2, PROMPT_VERSIONS, TracedModelClient, _apply_prompt_version
from obs.masking import find_unmasked
from obs.run_traced import F16_06_MESSAGE, run_case, run_message
from obs.tracing import Tracer


def case(case_id):
    from obs.run_traced import day15

    return next(item for item in day15.load_cases() if item["id"] == case_id)


def names(tracer):
    return [run.name for run in tracer.runs]


def types(tracer):
    return [run.run_type for run in tracer.runs]


# ── Trace shape ────────────────────────────────────────────────────────
def test_one_request_produces_one_root_trace():
    _, tracer = run_case(case("D15-01"), trace_dir=None)
    roots = [run for run in tracer.runs if run.parent_run_id is None]
    assert len(roots) == 1
    assert roots[0].name == "assistant_request"
    assert len({run.trace_id for run in tracer.runs}) == 1


def test_llm_retrieval_and_tool_each_get_a_typed_step():
    _, tracer = run_case(case("D15-01"), trace_dir=None)
    assert types(tracer) == ["chain", "llm", "tool", "retriever", "llm"]
    assert names(tracer) == [
        "assistant_request", "llm_call (1)", "lookup_internal_knowledge", "retrieve_policies", "llm_call (2)",
    ]


def test_retriever_step_nests_under_its_tool_step():
    _, tracer = run_case(case("D15-01"), trace_dir=None)
    tool = next(run for run in tracer.runs if run.name == "lookup_internal_knowledge")
    retriever = next(run for run in tracer.runs if run.run_type == "retriever")
    assert retriever.parent_run_id == tool.run_id


def test_llm_calls_are_numbered_in_order():
    _, tracer = run_case(case("D15-01"), trace_dir=None)
    assert [run.name for run in tracer.runs if run.run_type == "llm"] == ["llm_call (1)", "llm_call (2)"]


# ── Metadata ───────────────────────────────────────────────────────────
def test_every_run_carries_case_id_model_and_prompt_version():
    _, tracer = run_case(case("D15-08"), trace_dir=None, prompt_version="v1")
    root = tracer.root()
    assert root.metadata["case_id"] == "D15-08"
    assert root.metadata["prompt_version"] == "v1"
    for run in tracer.runs:
        assert run.metadata["model"]
        assert run.metadata["prompt_version"] == "v1"


def test_fault_name_is_recorded_on_every_run():
    _, tracer = run_case(case("D15-01"), faults=FaultConfig("slow_tool"), trace_dir=None)
    assert all(run.metadata["fault"] == "slow_tool" for run in tracer.runs)


# ── Errors are visible ─────────────────────────────────────────────────
def test_a_tool_returning_not_ok_is_marked_as_an_errored_step():
    _, tracer = run_case(case("D15-L02"), trace_dir=None)  # empty policy query
    errored = [run for run in tracer.runs if run.error]
    assert errored, "a rejected tool call must show as an error on its step"
    assert any(run.run_type == "tool" for run in errored)


def test_mcp_error_fault_surfaces_on_the_tool_step():
    _, tracer = run_case(case("D15-01"), faults=FaultConfig("mcp_error"), trace_dir=None)
    tool = next(run for run in tracer.runs if run.run_type == "tool")
    assert tool.error is not None and "MCP_TRANSPORT_ERROR" in tool.error


# ── Faults ─────────────────────────────────────────────────────────────
def test_no_fault_by_default_and_all_checks_pass():
    row, _ = run_case(case("D15-01"), trace_dir=None)
    assert row["fault"] is None
    assert all(row["checks"].values())


def test_bad_retrieval_empties_results_without_any_errored_step():
    row, tracer = run_case(case("D15-01"), faults=FaultConfig("bad_retrieval"), trace_dir=None)
    retriever = next(run for run in tracer.runs if run.run_type == "retriever")
    assert retriever.outputs["document_count"] == 0
    # The point of F16-04: nothing errors, yet the answer is wrong.
    assert not tracer.errors()
    assert row["checks"]["source_citation"] is False


def test_prompt_bloat_raises_the_input_token_estimate():
    _, plain = run_case(case("D15-01"), trace_dir=None)
    _, bloated = run_case(case("D15-01"), faults=FaultConfig("prompt_bloat"), trace_dir=None)

    def first_llm_tokens(tracer):
        return next(run for run in tracer.runs if run.run_type == "llm").metadata["approx_input_tokens"]

    assert first_llm_tokens(bloated) > first_llm_tokens(plain)


def test_slow_tool_makes_the_tool_step_the_slowest():
    _, tracer = run_case(case("D15-01"), faults=FaultConfig("slow_tool"), trace_dir=None)
    assert tracer.slowest().name == "lookup_internal_knowledge"


# ── The fix: bounded retry ─────────────────────────────────────────────
def test_without_retry_a_transient_failure_breaks_the_case():
    row, tracer = run_case(case("D15-01"), faults=FaultConfig("flaky_tool"), trace_dir=None, retry_attempts=0)
    assert row["checks"]["source_citation"] is False
    assert len([run for run in tracer.runs if run.run_type == "tool"]) == 1


def test_bounded_retry_recovers_the_case_and_shows_each_attempt():
    row, tracer = run_case(case("D15-01"), faults=FaultConfig("flaky_tool"), trace_dir=None, retry_attempts=2)
    tool_runs = [run for run in tracer.runs if run.run_type == "tool"]
    assert len(tool_runs) == 3
    assert [run.metadata["attempt"] for run in tool_runs] == [1, 2, 3]
    assert [bool(run.error) for run in tool_runs] == [True, True, False]
    assert all(row["checks"].values())


def test_retry_is_bounded_and_gives_up():
    # Three failures but only one retry allowed: the case must still fail
    # rather than loop. Guards against an unbounded retry.
    import obs.instrumented as instrumented

    original = instrumented.FLAKY_TOOL_FAILURES
    instrumented.FLAKY_TOOL_FAILURES = 99
    try:
        row, tracer = run_case(case("D15-01"), faults=FaultConfig("flaky_tool"), trace_dir=None, retry_attempts=1)
    finally:
        instrumented.FLAKY_TOOL_FAILURES = original
    assert len([run for run in tracer.runs if run.run_type == "tool"]) == 2
    assert row["checks"]["source_citation"] is False


def test_retry_does_not_retry_a_deterministic_validation_error():
    # D15-L02 sends an empty query: retrying cannot help, so there must be
    # exactly one attempt even with retries enabled.
    _, tracer = run_case(case("D15-L02"), trace_dir=None, retry_attempts=2)
    assert len([run for run in tracer.runs if run.run_type == "tool"]) == 1


def test_retry_changes_nothing_when_no_fault_is_active():
    plain, _ = run_case(case("D15-01"), trace_dir=None, retry_attempts=0)
    fixed, tracer = run_case(case("D15-01"), trace_dir=None, retry_attempts=2)
    assert plain["checks"] == fixed["checks"]
    assert len([run for run in tracer.runs if run.run_type == "tool"]) == 1


def test_negative_retry_is_rejected():
    from obs.instrumented import TracedToolRegistry

    with pytest.raises(ValueError):
        TracedToolRegistry(object(), Tracer(use_langsmith=False), retry_attempts=-1)


# ── Prompt versions ────────────────────────────────────────────────────
def test_prompt_version_replaces_only_the_system_message():
    messages = [{"role": "system", "content": PROMPT_V1}, {"role": "user", "content": "hi"}]
    swapped = _apply_prompt_version(messages, "v2")
    assert swapped[0]["content"] == PROMPT_V2
    assert swapped[1] == {"role": "user", "content": "hi"}


def test_v1_matches_the_day10_shipped_prompt():
    import sys
    from pathlib import Path

    day10 = Path(__file__).resolve().parents[2] / "10_tool_calling"
    sys.path.insert(0, str(day10))
    from src.assistant import SYSTEM_PROMPT

    assert PROMPT_VERSIONS["v1"] == SYSTEM_PROMPT


def test_unknown_prompt_version_is_rejected():
    with pytest.raises(ValueError, match="Unknown prompt_version"):
        TracedModelClient(object(), Tracer(use_langsmith=False), prompt_version="v9")


# ── Masking end to end ─────────────────────────────────────────────────
def test_personal_data_never_reaches_the_exported_trace():
    _, tracer = run_message(F16_06_MESSAGE, trace_dir=None)
    assert find_unmasked(tracer.records()) == []


def test_the_masked_placeholder_is_actually_present():
    _, tracer = run_message(F16_06_MESSAGE, trace_dir=None)
    root = tracer.root()
    assert "<masked:employee_id>" in root.inputs["message"]
    assert "<masked:email>" in root.inputs["message"]


def test_masking_also_covers_the_prompt_sent_to_the_model():
    # Input masking alone is not enough: the user text is echoed into the LLM
    # run's messages, so that payload must be masked too.
    _, tracer = run_message(F16_06_MESSAGE, trace_dir=None)
    llm = next(run for run in tracer.runs if run.run_type == "llm")
    assert find_unmasked(llm.inputs) == []


# ── Day 10 is untouched ────────────────────────────────────────────────
def test_tracing_does_not_change_the_assistants_answer():
    import run_baseline as day15

    traced, _ = run_case(case("D15-01"), trace_dir=None)
    untraced = day15.run_case(case("D15-01"))
    assert traced["assistant_output"] == untraced["assistant_output"]
    assert traced["checks"] == untraced["checks"]


def test_full_suite_still_passes_under_tracing():
    import run_baseline as day15

    for item in day15.load_cases():
        row, _ = run_case(item, trace_dir=None)
        assert all(row["checks"].values()), f"{item['id']} regressed under tracing: {row['checks']}"
