
import json
from types import SimpleNamespace
from typing import Literal

import httpx

try:
    import ollama
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency is absent
    class _OllamaResponseError(Exception):
        def __init__(self, message="", status_code=None, error=None):
            super().__init__(message)
            self.status_code = status_code
            self.error = error

    class _OllamaClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "The 'ollama' package is not installed. "
                "Install it before using the client."
            )

    ollama = SimpleNamespace(
        ResponseError=_OllamaResponseError,
        Client=_OllamaClient,
    )

from pydantic import BaseModel, Field, StrictStr, ValidationError


MAX_ATTEMPTS = 2


# 1. Output contract
class AIResponse(BaseModel):
    status: Literal["success", "needs_clarification"]
    answer: StrictStr = Field(min_length=1)

    class Config:
        extra = "forbid"


# 2. Get JSON Schema
def get_response_schema():
    if hasattr(AIResponse, "model_json_schema"):
        return AIResponse.model_json_schema()

    return AIResponse.schema()


# 3. Parse JSON and validate fields
def validate_response(raw_output):
    parsed = json.loads(raw_output)

    if hasattr(AIResponse, "model_validate"):
        return AIResponse.model_validate(parsed)

    return AIResponse.parse_obj(parsed)


# 4. Convert validated response to a dictionary
def response_to_dict(result):
    if hasattr(result, "model_dump"):
        return result.model_dump()

    return result.dict()


# 5. Generate a response with bounded retry and fallback
def generate_validated_response(
    client,
    model,
    messages,
    max_attempts=MAX_ATTEMPTS,
):
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    working_messages = list(messages)
    last_error = "No response was produced."

    for attempt in range(1, max_attempts + 1):

        # Request structured JSON from Ollama.
        try:
            response = client.chat(
                model=model,
                messages=working_messages,
                format=get_response_schema(),
                stream=False,
                options={
                    "temperature": 0,
                    "num_ctx": 2048,
                },
            )

        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            ConnectionError,
        ) as exc:
            last_error = f"{type(exc).__name__}: {exc}"

            if attempt < max_attempts:
                continue

            break

        except ollama.ResponseError as exc:
            status_code = getattr(exc, "status_code", None)
            last_error = (
                f"Ollama error (HTTP {status_code}): {exc.error}"
            )

            retryable = (
                status_code == 429
                or (
                    status_code is not None
                    and status_code >= 500
                )
            )

            if retryable and attempt < max_attempts:
                continue

            break

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            break

        # Parse and validate the returned JSON.
        raw_output = response.message.content or ""

        try:
            result = validate_response(raw_output)
            return result, None

        except (
            json.JSONDecodeError,
            ValidationError,
            TypeError,
            ValueError,
        ) as exc:
            last_error = f"{type(exc).__name__}: {exc}"

            if attempt < max_attempts:
                working_messages.extend([
                    {
                        "role": "assistant",
                        "content": raw_output,
                    },
                    {
                        "role": "user",
                        "content": (
                            "Your previous response failed JSON "
                            "parsing or schema validation. Return "
                            "one corrected JSON object matching "
                            "the required schema. Do not add "
                            "surrounding text."
                        ),
                    },
                ])

    # Failure after the allowed attempts.
    return None, last_error
