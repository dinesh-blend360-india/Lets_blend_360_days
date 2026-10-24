"""Atomic persistence for simulated local service requests only."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


class ServiceRequestStore:
    def __init__(self, actions_dir: str | Path):
        self.actions_dir = Path(actions_dir)

    def create(self, args: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        request_id = f"SR-{uuid4().hex[:12].upper()}"
        record = {
            "request_id": request_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "title": args["title"],
            "description": args["description"],
            "priority": args["priority"],
            "simulated": True,
        }
        self._persist(request_id, record)
        return {
            "ok": True,
            "tool_name": "create_service_request",
            "status": "created",
            "request_id": request_id,
            "simulated": True,
        }

    def _persist(self, request_id: str, record: dict[str, Any]) -> None:
        self.actions_dir.mkdir(parents=True, exist_ok=True)
        target = self.actions_dir / f"{request_id}.json"
        temporary = self.actions_dir / f".{request_id}.{uuid4().hex}.tmp"
        try:
            with temporary.open("x", encoding="utf-8", newline="") as handle:
                json.dump(record, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()


def proposal_summary(args: dict[str, Any]) -> str:
    return (
        "Proposed simulated service request:\n"
        f"  Title: {args['title']}\n"
        f"  Priority: {args['priority']}\n"
        f"  Description: {args['description']}\n"
        "Type CONFIRM to create this local simulated record."
    )

