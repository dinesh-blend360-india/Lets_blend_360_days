import json

from src.config import ActorContext
from src.execution_logger import ExecutionLogger
from src.knowledge_lookup import KnowledgeLookup
from src.service_request import ServiceRequestStore
from src.tool_registry import ToolRegistry


def registry(app_config):
    return ToolRegistry(KnowledgeLookup(app_config), ServiceRequestStore(app_config.actions_dir), ExecutionLogger(app_config.log_file))


ARGS = {"title": "Request database access", "description": "Needed for analytics.", "priority": "normal"}


def test_confirmed_action_creates_one_atomic_record(app_config):
    summaries = []
    result = registry(app_config).execute(
        tool_name="create_service_request", raw_arguments=ARGS,
        actor=ActorContext("employee-1", True), confirmation_handler=lambda text: summaries.append(text) or True,
        call_id="confirmed",
    )
    files = list(app_config.actions_dir.glob("*.json"))
    assert result["status"] == "created"
    assert len(files) == 1
    assert not list(app_config.actions_dir.glob("*.tmp"))
    record = json.loads(files[0].read_text(encoding="utf-8"))
    assert record["actor_id"] == "employee-1"
    assert record["simulated"] is True
    assert "Type CONFIRM" in summaries[0]


def test_rejected_confirmation_creates_nothing(app_config):
    result = registry(app_config).execute(
        tool_name="create_service_request", raw_arguments=ARGS,
        actor=ActorContext("employee-1", True), confirmation_handler=lambda _: False,
    )
    assert result["status"] == "cancelled"
    assert not app_config.actions_dir.exists()


def test_failed_persistence_never_claims_success(app_config):
    store = ServiceRequestStore(app_config.actions_dir)
    store._persist = lambda *args: (_ for _ in ()).throw(OSError("disk full"))
    tools = ToolRegistry(KnowledgeLookup(app_config), store, ExecutionLogger(app_config.log_file))
    result = tools.execute(
        tool_name="create_service_request", raw_arguments=ARGS,
        actor=ActorContext("employee-1", True), confirmation_handler=lambda _: True,
    )
    assert result["status"] == "execution_error"
    assert result["error"]["code"] == "PERSISTENCE_FAILED"

