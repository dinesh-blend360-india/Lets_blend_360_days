"""Bounded JSON Lines audit logging with defensive redaction."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any


SENSITIVE_KEYS = {"password", "token", "api_key", "authorization", "secret"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def bounded_argument_summary(tool_name: str, args: dict[str, Any] | None) -> dict[str, Any]:
    args = args or {}
    if tool_name == "create_service_request":
        return {
            "title_length": len(str(args.get("title", ""))),
            "description_length": len(str(args.get("description", ""))),
            "priority": args.get("priority"),
        }
    if tool_name == "lookup_internal_knowledge":
        return {
            "query_length": len(str(args.get("query", ""))),
            "category": args.get("category"),
            "top_k": args.get("top_k"),
        }
    return {"provided_keys": sorted(args)}


class ExecutionLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def log(self, event: dict[str, Any]) -> None:
        record = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **redact(event)}
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(line)
            handle.flush()

