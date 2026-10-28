import asyncio
from pathlib import Path
import sys

from mcp import Client


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from server import mcp
from client import payload


def test_discovery_success_and_validation_failure(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_BACKEND", "mock")

    async def check():
        async with Client(mcp) as client:
            capabilities = await client.list_tools()
            assert [tool.name for tool in capabilities.tools] == ["lookup_internal_knowledge"]
            result = await client.call_tool("lookup_internal_knowledge", {"query": "expense claim deadline"})
            assert payload(result)["ok"] is True
            assert payload(result)["backend"] == "mock"
            failure = await client.call_tool("lookup_internal_knowledge", {"query": ""})
            assert failure.is_error is True
            assert payload(failure)["error"]["code"] == "EMPTY_ARGUMENT"

    asyncio.run(check())
