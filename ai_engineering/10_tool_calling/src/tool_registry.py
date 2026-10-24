"""Closed tool registry enforcing parse, validation, permission, confirmation, execution, result validation, and logging."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from .config import ActorContext
from .execution_logger import ExecutionLogger, bounded_argument_summary
from .knowledge_lookup import KnowledgeLookup
from .service_request import ServiceRequestStore, proposal_summary
from .tool_schemas import (
    TOOL_DEFINITIONS, ToolValidationError, validate_action_result, validate_create_arguments,
    validate_lookup_arguments, validate_lookup_result,
)


ConfirmationHandler = Callable[[str], bool]


class ToolRegistry:
    def __init__(self, lookup: KnowledgeLookup, store: ServiceRequestStore, logger: ExecutionLogger):
        self.lookup = lookup
        self.store = store
        self.logger = logger
        self._processed_call_ids: set[tuple[str, str]] = set()

    @property
    def definitions(self) -> list[dict[str, Any]]:
        return TOOL_DEFINITIONS

    def execute(self, *, tool_name: str, raw_arguments: Any, actor: ActorContext, confirmation_handler: ConfirmationHandler, call_id: str | None = None, correlation_id: str | None = None) -> dict[str, Any]:
        started = perf_counter()
        correlation_id = correlation_id or uuid4().hex
        call_id = call_id or uuid4().hex
        event: dict[str, Any] = {
            "correlation_id": correlation_id, "call_id": call_id, "tool_name": tool_name,
            "argument_validation": "not_started", "permission_decision": "not_applicable",
            "confirmation_result": "not_applicable", "execution_status": "not_started",
            "result_validation": "not_started", "simulated": tool_name == "create_service_request",
        }
        result: dict[str, Any]
        try:
            call_key = (correlation_id, call_id)
            if call_key in self._processed_call_ids:
                raise ToolValidationError("DUPLICATE_TOOL_CALL", "This tool call ID was already processed")
            self._processed_call_ids.add(call_key)
            if tool_name not in {"lookup_internal_knowledge", "create_service_request"}:
                raise ToolValidationError("UNKNOWN_TOOL", f"Tool is not registered: {tool_name}")
            args = self._parse_arguments(raw_arguments)
            if tool_name == "lookup_internal_knowledge":
                validated = validate_lookup_arguments(args)
                event["argument_validation"] = "passed"
                event["validated_argument_summary"] = bounded_argument_summary(tool_name, validated)
                result = self.lookup.lookup(**validated)
                event["execution_status"] = "succeeded"
                validate_lookup_result(result)
            else:
                validated = validate_create_arguments(args)
                event["argument_validation"] = "passed"
                event["validated_argument_summary"] = bounded_argument_summary(tool_name, validated)
                if not actor.can_create_service_request:
                    event["permission_decision"] = "denied"
                    event["execution_status"] = "permission_denied"
                    result = self._action_failure("permission_denied", "PERMISSION_DENIED", "Actor is not allowed to create service requests")
                else:
                    event["permission_decision"] = "allowed"
                    confirmed = bool(confirmation_handler(proposal_summary(validated)))
                    event["confirmation_result"] = "confirmed" if confirmed else "rejected"
                    if not confirmed:
                        event["execution_status"] = "cancelled"
                        result = self._action_failure("cancelled", "CONFIRMATION_REJECTED", "The user did not confirm the proposed action")
                    else:
                        try:
                            result = self.store.create(validated, actor_id=actor.actor_id)
                            event["execution_status"] = "succeeded"
                        except Exception as exc:
                            result = self._action_failure("execution_error", "PERSISTENCE_FAILED", f"The simulated request could not be saved: {type(exc).__name__}")
                            event["execution_status"] = "failed"
                validate_action_result(result)
            event["result_validation"] = "passed"
        except ToolValidationError as exc:
            invalid_result = exc.code == "INVALID_TOOL_RESULT"
            if invalid_result:
                event["result_validation"] = "failed"
                event["execution_status"] = "failed"
            else:
                event["argument_validation"] = "failed" if event["argument_validation"] == "not_started" else event["argument_validation"]
                event["execution_status"] = "rejected"
            event["error_code"] = exc.code
            result = {"ok": False, "tool_name": tool_name, "status": "execution_error" if invalid_result else "validation_error", "error": {"code": exc.code, "message": str(exc)}}
        except Exception as exc:
            event["execution_status"] = "failed"
            event["error_code"] = "TOOL_EXECUTION_FAILED"
            result = {"ok": False, "tool_name": tool_name, "status": "execution_error", "error": {"code": "TOOL_EXECUTION_FAILED", "message": f"Controlled tool failure: {type(exc).__name__}"}}
        event["duration_ms"] = round((perf_counter() - started) * 1000, 3)
        if not result.get("ok") and "error" in result:
            event["error_code"] = result["error"]["code"]
        try:
            self.logger.log(event)
        except Exception as exc:
            result.setdefault("warnings", []).append({"code": "AUDIT_LOG_FAILED", "message": f"Audit event could not be written: {type(exc).__name__}"})
        return result

    @staticmethod
    def _parse_arguments(raw: Any) -> dict[str, Any]:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ToolValidationError("MALFORMED_JSON", f"Tool arguments are not valid JSON: {exc.msg}") from exc
        if not isinstance(raw, dict):
            raise ToolValidationError("INVALID_ARGUMENT_TYPE", "Tool arguments must be a JSON object")
        return raw

    @staticmethod
    def _action_failure(status: str, code: str, message: str) -> dict[str, Any]:
        return {"ok": False, "tool_name": "create_service_request", "status": status, "error": {"code": code, "message": message}, "simulated": True}

