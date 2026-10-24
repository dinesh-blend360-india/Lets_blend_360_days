import json

from src.config import ActorContext
from src.execution_logger import ExecutionLogger
from src.knowledge_lookup import KnowledgeLookup
from src.service_request import ServiceRequestStore
from src.tool_registry import ToolRegistry


def test_jsonl_log_contains_traceability_and_no_free_text(app_config):
    registry = ToolRegistry(KnowledgeLookup(app_config), ServiceRequestStore(app_config.actions_dir), ExecutionLogger(app_config.log_file))
    registry.execute(
        tool_name="create_service_request",
        raw_arguments={"title": "Secret project", "description": "token abc123 password hunter2", "priority": "high"},
        actor=ActorContext("user", True), confirmation_handler=lambda _: False, call_id="log-1", correlation_id="corr-1",
    )
    lines = app_config.log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["correlation_id"] == "corr-1"
    assert event["tool_name"] == "create_service_request"
    assert event["confirmation_result"] == "rejected"
    assert event["duration_ms"] >= 0
    assert "Secret project" not in lines[0]
    assert "abc123" not in lines[0]
    assert "hunter2" not in lines[0]


def test_invalid_input_is_logged_without_execution(app_config):
    registry = ToolRegistry(KnowledgeLookup(app_config), ServiceRequestStore(app_config.actions_dir), ExecutionLogger(app_config.log_file))
    result = registry.execute(
        tool_name="lookup_internal_knowledge", raw_arguments={"query": "", "top_k": 99},
        actor=ActorContext("user", False), confirmation_handler=lambda _: False,
    )
    event = json.loads(app_config.log_file.read_text(encoding="utf-8").splitlines()[0])
    assert result["status"] == "validation_error"
    assert event["argument_validation"] == "failed"
    assert event["execution_status"] == "rejected"


def test_audit_log_failure_is_reported_without_hiding_tool_outcome(app_config):
    class BrokenLogger:
        def log(self, event):
            raise OSError("read only")

    registry = ToolRegistry(KnowledgeLookup(app_config), ServiceRequestStore(app_config.actions_dir), BrokenLogger())
    result = registry.execute(
        tool_name="lookup_internal_knowledge", raw_arguments={"query": "expense", "top_k": 1},
        actor=ActorContext("user", False), confirmation_handler=lambda _: False,
    )
    assert result["ok"] is True
    assert result["warnings"][0]["code"] == "AUDIT_LOG_FAILED"

