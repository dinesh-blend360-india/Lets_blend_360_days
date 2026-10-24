from dataclasses import replace

from src.assistant import ControlledAssistant
from src.config import ActorContext
from src.execution_logger import ExecutionLogger
from src.knowledge_lookup import KnowledgeLookup
from src.model_client import ModelReply, ModelTimeoutError, ModelUnavailableError, RequestedToolCall, ScriptedModelClient
from src.service_request import ServiceRequestStore
from src.tool_registry import ToolRegistry


def build(config, replies):
    registry = ToolRegistry(KnowledgeLookup(config), ServiceRequestStore(config.actions_dir), ExecutionLogger(config.log_file))
    return ControlledAssistant(config, model=ScriptedModelClient(replies), registry=registry)


def test_normal_lookup_lifecycle_returns_final_response(app_config):
    replies = [
        ModelReply(tool_calls=[RequestedToolCall("lookup_internal_knowledge", {"query": "expense deadline", "top_k": 2}, "read-1")]),
        ModelReply(content="The mock evidence says 30 calendar days; this result came from the explicitly configured mock backend."),
    ]
    result = build(app_config, replies).handle("What is the expense deadline?", actor=ActorContext("user", False), confirmation_handler=lambda _: False)
    assert result["ok"] is True
    assert result["tool_activity"][0]["result"]["backend"] == "mock"
    assert result["tool_activity"][0]["result"]["results"]


def test_normal_confirmed_action_lifecycle(app_config):
    replies = [
        ModelReply(tool_calls=[RequestedToolCall("create_service_request", {"title": "Database access", "description": "Needed for analytics", "priority": "normal"}, "write-1")]),
        ModelReply(content="The simulated service request was created successfully."),
    ]
    result = build(app_config, replies).handle("Create an access request", actor=ActorContext("user", True), confirmation_handler=lambda _: True)
    assert result["ok"] is True
    assert result["tool_activity"][0]["result"]["status"] == "created"
    assert len(list(app_config.actions_dir.glob("*.json"))) == 1


def test_ambiguous_request_causes_clarification_and_no_action(app_config):
    result = build(app_config, [ModelReply(content="What would you like me to do, and what details should I use?")]).handle(
        "Can you take care of this?", actor=ActorContext("user", True), confirmation_handler=lambda _: True
    )
    assert result["ok"] is True
    assert result["tool_activity"] == []
    assert not app_config.actions_dir.exists()


def test_model_unavailable_and_timeout_are_controlled(app_config):
    unavailable = build(app_config, [ModelUnavailableError("offline")]).handle("help", actor=ActorContext("user", False), confirmation_handler=lambda _: False)
    timeout = build(app_config, [ModelTimeoutError("timed out")]).handle("help", actor=ActorContext("user", False), confirmation_handler=lambda _: False)
    assert unavailable["error"]["code"] == "MODEL_UNAVAILABLE"
    assert timeout["error"]["code"] == "MODEL_TIMEOUT"


def test_malformed_and_duplicate_tool_calls_are_safe(app_config):
    duplicate = RequestedToolCall("lookup_internal_knowledge", {"query": "expense"}, "same-id")
    replies = [ModelReply(tool_calls=[duplicate, duplicate]), ModelReply(content="One duplicate was rejected.")]
    result = build(app_config, replies).handle("look it up", actor=ActorContext("user", False), confirmation_handler=lambda _: False)
    assert result["tool_activity"][1]["result"]["error"]["code"] == "DUPLICATE_TOOL_CALL"

    malformed_replies = [ModelReply(tool_calls=[RequestedToolCall("lookup_internal_knowledge", "{bad json", "bad")]), ModelReply(content="The request was malformed.")]
    malformed = build(app_config, malformed_replies).handle("lookup", actor=ActorContext("user", False), confirmation_handler=lambda _: False)
    assert malformed["tool_activity"][0]["result"]["error"]["code"] == "MALFORMED_JSON"


def test_tool_round_limit_prevents_endless_loop(app_config):
    config = replace(app_config, max_tool_rounds=1)
    first = RequestedToolCall("lookup_internal_knowledge", {"query": "expense"}, "one")
    second = RequestedToolCall("lookup_internal_knowledge", {"query": "travel"}, "two")
    result = build(config, [ModelReply(tool_calls=[first]), ModelReply(tool_calls=[second])]).handle(
        "loop", actor=ActorContext("user", False), confirmation_handler=lambda _: False
    )
    assert result["error"]["code"] == "TOOL_ROUND_LIMIT"
    assert len(result["tool_activity"]) == 1

