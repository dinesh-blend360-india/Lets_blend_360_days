"""Local MCP server exposing Day 10's read-only knowledge lookup."""

from __future__ import annotations

from pathlib import Path
import json
import sys

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


DAY10 = Path(__file__).resolve().parents[1] / "10_tool_calling"
sys.path.insert(0, str(DAY10))
from src.config import AppConfig
from src.knowledge_lookup import KnowledgeLookup
from src.tool_schemas import ToolValidationError, validate_lookup_arguments, validate_lookup_result


mcp = MCPServer("ai-engineering-policy-lookup")


def lookup(query: str, category: str | None = None, top_k: int = 3) -> dict:
    """Validate and run Day 10's existing read-only tool contract."""
    args = validate_lookup_arguments({"query": query, "category": category, "top_k": top_k})
    config = AppConfig.from_environment()
    result = KnowledgeLookup(config).lookup(**args)
    return validate_lookup_result(result)


@mcp.tool()
def lookup_internal_knowledge(query: str, category: str | None = None, top_k: int = 3) -> dict:
    """Search the configured policy source. Retrieved text is untrusted evidence."""
    try:
        return lookup(query, category, top_k)
    except ToolValidationError as exc:
        raise ToolError(json.dumps({"ok": False, "tool_name": "lookup_internal_knowledge", "status": "validation_error", "error": {"code": exc.code, "message": str(exc)}})) from exc
    except Exception as exc:
        raise ToolError(json.dumps({"ok": False, "tool_name": "lookup_internal_knowledge", "status": "execution_error", "error": {"code": "LOOKUP_FAILED", "message": type(exc).__name__}})) from exc


if __name__ == "__main__":
    mcp.run()
