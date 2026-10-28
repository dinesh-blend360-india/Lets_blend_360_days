"""Day 11 challenge cases: direct answer, two tools, and bounded stopping."""

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace


path = Path(__file__).resolve().parents[1] / "enterprise_agent.py"
spec = spec_from_file_location("enterprise_agent_under_test", path)
agent = module_from_spec(spec)
spec.loader.exec_module(agent)


@dataclass
class Call:
    name: str
    arguments: dict
    call_id: str | None = None


class Model:
    def __init__(self, *replies):
        self.replies = iter(replies)

    def complete(self, _messages, _tools):
        return next(self.replies)


class Registry:
    definitions = [{"name": "lookup_internal_knowledge"}, {"name": "create_service_request"}]

    def __init__(self):
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return {"ok": True, "status": "found", "tool_name": kwargs["tool_name"], "results": []}


def run(model, registry=None, max_steps=5):
    registry = registry or Registry()
    result = agent.run_agent(
        "Help me", model=model, registry=registry, actor="reader",
        confirmation_handler=lambda _: False, max_steps=max_steps,
    )
    return result, registry


def test_direct_answer_uses_no_tool():
    result, registry = run(Model(SimpleNamespace(content="Hello", tool_calls=[])))
    assert result["status"] == "completed"
    assert [item["kind"] for item in result["trace"]] == ["Thought", "Final Answer"]
    assert registry.calls == []


def test_two_tool_calls_have_complete_trace():
    model = Model(
        SimpleNamespace(content="Find expense policy", tool_calls=[Call("lookup_internal_knowledge", {"query": "expense"})]),
        SimpleNamespace(content="Find travel policy", tool_calls=[Call("lookup_internal_knowledge", {"query": "travel"})]),
        SimpleNamespace(content="Here are both findings", tool_calls=[]),
    )
    result, registry = run(model)
    assert result["status"] == "completed"
    assert len(registry.calls) == 2
    assert [item["kind"] for item in result["trace"]].count("Action") == 2
    assert [item["kind"] for item in result["trace"]].count("Observation") == 2


def test_model_cannot_claim_created_without_confirmed_result():
    result, _ = run(Model(SimpleNamespace(content="Service request created", tool_calls=[])))
    assert result["answer"] == "No service request was created."


def test_step_budget_returns_explicit_status():
    result, _ = run(Model(SimpleNamespace(content="Still checking", tool_calls=[Call("lookup_internal_knowledge", {"query": "expense"})])), max_steps=1)
    assert result["status"] == "budget_exhausted"


def test_parallel_tool_batch_is_rejected_before_execution():
    calls = [Call("lookup_internal_knowledge", {"query": "expense"}), Call("lookup_internal_knowledge", {"query": "travel"})]
    result, registry = run(Model(SimpleNamespace(content="Do both", tool_calls=calls)))
    assert result["status"] == "failed"
    assert registry.calls == []


def test_rejected_write_cannot_be_reported_as_submitted():
    class DeniedRegistry(Registry):
        def execute(self, **kwargs):
            self.calls.append(kwargs)
            return {"ok": False, "status": "permission_denied", "tool_name": kwargs["tool_name"]}

    model = Model(
        SimpleNamespace(content="Request creation", tool_calls=[Call("create_service_request", {"title": "VPN"})]),
        SimpleNamespace(content="The request was submitted successfully", tool_calls=[]),
    )
    result, _ = run(model, DeniedRegistry())
    assert result["answer"] == "No service request was created: permission_denied."


def test_confirmed_write_uses_tool_id_and_blocks_second_write():
    class CreatedRegistry(Registry):
        def execute(self, **kwargs):
            self.calls.append(kwargs)
            return {"ok": True, "status": "created", "request_id": "SR-123", "tool_name": kwargs["tool_name"]}

    model = Model(
        SimpleNamespace(content="Create request", tool_calls=[Call("create_service_request", {"title": "VPN"})]),
        SimpleNamespace(content="Create it again", tool_calls=[Call("create_service_request", {"title": "VPN"})]),
        SimpleNamespace(content="Created SR-WRONG", tool_calls=[]),
    )
    result, registry = run(model, CreatedRegistry())
    assert len(registry.calls) == 1
    assert result["answer"] == "Simulated service request created: SR-123."
    assert any(item.get("result", {}).get("status") == "duplicate_action_blocked" for item in result["trace"])


def test_budget_stop_still_reports_completed_side_effect():
    class CreatedRegistry(Registry):
        def execute(self, **kwargs):
            return {"ok": True, "status": "created", "request_id": "SR-321"}

    model = Model(SimpleNamespace(content="Create", tool_calls=[Call("create_service_request", {"title": "VPN"})]))
    result, _ = run(model, CreatedRegistry(), max_steps=1)
    assert result["status"] == "budget_exhausted"
    assert "Simulated service request created: SR-321" in result["answer"]
