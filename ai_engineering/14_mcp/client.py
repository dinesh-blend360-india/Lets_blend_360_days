"""Discover and exercise the local Day 14 MCP server over stdio."""

import asyncio
import json
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters


def payload(result) -> dict:
    if result.structured_content is not None:
        return result.structured_content
    text = result.content[0].text
    start = text.find("{")
    return json.loads(text[start:]) if start >= 0 else {"ok": False, "error": {"message": text}}


async def run() -> dict:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).with_name("server.py"))],
        env={"KNOWLEDGE_BACKEND": "mock"},
    )
    async with Client(server) as client:
        discovered = await client.list_tools()
        success = await client.call_tool("lookup_internal_knowledge", {"query": "expense claim deadline", "top_k": 2})
        failure = await client.call_tool("lookup_internal_knowledge", {"query": ""})
        return {
            "capabilities": [
                {"name": item.name, "description": item.description, "input_schema": item.input_schema}
                for item in discovered.tools
            ],
            "success": {"is_error": success.is_error, "result": payload(success)},
            "failure": {"is_error": failure.is_error, "result": payload(failure)},
        }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(run()), indent=2, ensure_ascii=False))
