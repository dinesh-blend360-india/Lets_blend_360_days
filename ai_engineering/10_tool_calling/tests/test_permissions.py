from src.config import ActorContext
from src.execution_logger import ExecutionLogger
from src.knowledge_lookup import KnowledgeLookup
from src.service_request import ServiceRequestStore
from src.tool_registry import ToolRegistry


ARGS = {"title": "Access", "description": "Need access", "priority": "low"}


def make_registry(config):
    return ToolRegistry(KnowledgeLookup(config), ServiceRequestStore(config.actions_dir), ExecutionLogger(config.log_file))


def test_permission_denial_happens_before_confirmation(app_config):
    confirmations = []
    result = make_registry(app_config).execute(
        tool_name="create_service_request", raw_arguments=ARGS,
        actor=ActorContext("unauthorized", False), confirmation_handler=lambda text: confirmations.append(text) or True,
    )
    assert result["status"] == "permission_denied"
    assert confirmations == []
    assert not app_config.actions_dir.exists()


def test_unknown_tool_and_model_controlled_actor_are_rejected(app_config):
    registry = make_registry(app_config)
    unknown = registry.execute(tool_name="run_shell", raw_arguments={"command": "whoami"}, actor=ActorContext("user", True), confirmation_handler=lambda _: True)
    spoof = registry.execute(tool_name="create_service_request", raw_arguments={**ARGS, "actor": "admin"}, actor=ActorContext("user", True), confirmation_handler=lambda _: True)
    assert unknown["error"]["code"] == "UNKNOWN_TOOL"
    assert spoof["error"]["code"] == "UNKNOWN_ARGUMENT"
    assert not app_config.actions_dir.exists()

