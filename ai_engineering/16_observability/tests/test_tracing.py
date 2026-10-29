import json

import pytest

from obs.tracing import Tracer, render_tree


def test_nesting_sets_parent_and_shares_trace_id():
    tracer = Tracer(use_langsmith=False)
    with tracer.run("root", "chain", {}):
        with tracer.run("child", "tool", {}):
            pass
    root, child = tracer.runs
    assert root.parent_run_id is None
    assert child.parent_run_id == root.run_id
    assert child.trace_id == root.trace_id


def test_siblings_share_one_parent():
    tracer = Tracer(use_langsmith=False)
    with tracer.run("root", "chain", {}):
        with tracer.run("a", "llm", {}):
            pass
        with tracer.run("b", "llm", {}):
            pass
    root, first, second = tracer.runs
    assert first.parent_run_id == second.parent_run_id == root.run_id


def test_exception_is_recorded_and_reraised():
    tracer = Tracer(use_langsmith=False)
    with pytest.raises(ValueError):
        with tracer.run("boom", "tool", {}):
            raise ValueError("tool exploded")
    run = tracer.runs[0]
    assert run.error is not None and "tool exploded" in run.error
    assert run.end_time is not None


def test_stack_unwinds_after_error_so_later_runs_are_not_nested():
    tracer = Tracer(use_langsmith=False)
    with pytest.raises(ValueError):
        with tracer.run("boom", "tool", {}):
            raise ValueError("x")
    with tracer.run("next", "llm", {}):
        pass
    assert tracer.runs[1].parent_run_id is None


def test_inputs_and_outputs_are_masked_on_the_run():
    tracer = Tracer(use_langsmith=False)
    with tracer.run("root", "chain", {"message": "I am E1023"}) as run:
        tracer.end_run(run, outputs={"answer": "mail a.b@example.com"})
    assert tracer.runs[0].inputs == {"message": "I am <masked:employee_id>"}
    assert tracer.runs[0].outputs == {"answer": "mail <masked:email>"}


def test_base_metadata_is_applied_to_every_run():
    tracer = Tracer(use_langsmith=False, base_metadata={"model": "m", "prompt_version": "v1"})
    with tracer.run("root", "chain", {}):
        with tracer.run("child", "tool", {}, tool_name="t"):
            pass
    assert all(run.metadata["prompt_version"] == "v1" for run in tracer.runs)
    assert tracer.runs[1].metadata["tool_name"] == "t"


def test_summary_reports_slowest_and_errors():
    tracer = Tracer(use_langsmith=False)
    with tracer.run("root", "chain", {}):
        with tracer.run("ok", "llm", {}):
            pass
        bad = tracer.start_run("bad", "tool", {})
        tracer.end_run(bad, error="TOOL_TIMEOUT")
    summary = tracer.summary()
    assert summary["step_count"] == 3
    assert summary["slowest_step"] is not None
    assert [item["name"] for item in summary["error_steps"]] == ["bad"]
    assert set(summary["ms_by_run_type"]) == {"llm", "tool"}


def test_flush_writes_one_record_per_run_with_required_fields(tmp_path):
    tracer = Tracer(tmp_path, use_langsmith=False)
    with tracer.run("root", "chain", {}):
        with tracer.run("child", "tool", {}):
            pass
    path = tracer.flush()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    required = {
        "run_id", "parent_run_id", "trace_id", "name", "run_type",
        "start_time", "end_time", "inputs", "outputs", "error", "metadata",
    }
    assert required <= set(records[0])


def test_flush_without_trace_dir_is_a_noop():
    tracer = Tracer(None, use_langsmith=False)
    with tracer.run("root", "chain", {}):
        pass
    assert tracer.flush() is None


def test_langsmith_is_off_unless_requested():
    assert Tracer(use_langsmith=False).backend == "local"


def test_render_tree_indents_children_and_marks_errors():
    tracer = Tracer(use_langsmith=False)
    with tracer.run("root", "chain", {}):
        bad = tracer.start_run("bad", "tool", {})
        tracer.end_run(bad, error="boom")
    rendered = render_tree(tracer.records())
    lines = rendered.splitlines()
    assert lines[0].startswith("root")
    assert lines[1].startswith("  bad")
    assert "ERROR" in lines[1]
