import os

import pytest

from src.assistant import ControlledAssistant
from src.config import AppConfig, ActorContext


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DAY10_INTEGRATION") != "1", reason="set RUN_DAY10_INTEGRATION=1 after verifying Ollama and the configured model")
def test_live_ollama_read_tool_call():
    config = AppConfig.from_environment()
    result = ControlledAssistant(config).handle(
        "Use the knowledge lookup tool to find the expense claim deadline.",
        actor=ActorContext("integration-user", False), confirmation_handler=lambda _: False,
    )
    assert result["ok"] is True
    assert any(item["tool_name"] == "lookup_internal_knowledge" for item in result["tool_activity"])

