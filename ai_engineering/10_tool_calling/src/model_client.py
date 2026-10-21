"""Native Ollama tool-call adapter and deterministic scripted test client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .config import AppConfig


class ModelClientError(RuntimeError):
    code = "MODEL_ERROR"


class ModelUnavailableError(ModelClientError):
    code = "MODEL_UNAVAILABLE"


class ModelTimeoutError(ModelClientError):
    code = "MODEL_TIMEOUT"


@dataclass(frozen=True)
class RequestedToolCall:
    name: str
    arguments: Any
    call_id: str | None = None


@dataclass(frozen=True)
class ModelReply:
    content: str = ""
    tool_calls: list[RequestedToolCall] = field(default_factory=list)


class ModelClient(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelReply: ...


def _get(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, dict) else getattr(value, key, default)


class OllamaModelClient:
    def __init__(self, config: AppConfig, client: Any | None = None):
        self.config = config
        if client is not None:
            self.client = client
            return
        try:
            import ollama
        except ImportError as exc:
            raise ModelUnavailableError("The Ollama Python package is not installed") from exc
        try:
            self.client = ollama.Client(host=config.ollama_base_url, timeout=config.model_timeout_seconds)
        except Exception as exc:
            raise ModelUnavailableError(f"Could not initialize Ollama at {config.ollama_base_url}") from exc

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelReply:
        try:
            response = self.client.chat(model=self.config.ollama_model, messages=messages, tools=tools, stream=False)
        except TimeoutError as exc:
            raise ModelTimeoutError(f"Ollama request exceeded {self.config.model_timeout_seconds} seconds") from exc
        except Exception as exc:
            name = type(exc).__name__.casefold()
            if "timeout" in name:
                raise ModelTimeoutError(f"Ollama request exceeded {self.config.model_timeout_seconds} seconds") from exc
            raise ModelUnavailableError(f"Ollama model '{self.config.ollama_model}' is unavailable at {self.config.ollama_base_url}") from exc
        message = _get(response, "message", response)
        content = _get(message, "content", "") or ""
        calls = []
        for call in _get(message, "tool_calls", []) or []:
            function = _get(call, "function", call)
            calls.append(RequestedToolCall(
                name=str(_get(function, "name", "")),
                arguments=_get(function, "arguments", {}),
                call_id=_get(call, "id"),
            ))
        return ModelReply(content=str(content), tool_calls=calls)


class ScriptedModelClient:
    """Deterministic client for tests and offline demonstrations."""

    def __init__(self, replies: list[ModelReply | Exception]):
        self.replies = list(replies)
        self.requests: list[dict[str, Any]] = []

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelReply:
        self.requests.append({"messages": list(messages), "tools": tools})
        if not self.replies:
            raise ModelClientError("Scripted model has no remaining replies")
        value = self.replies.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

