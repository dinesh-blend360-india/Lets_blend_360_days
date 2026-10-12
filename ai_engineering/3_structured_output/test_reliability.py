import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from pydantic import ValidationError

from reliability import (
    AIResponse,
    validate_response,
    generate_validated_response,
)


# ==================================================
# Test data and helpers
# ==================================================

VALID_JSON = json.dumps({
    "status": "success",
    "answer": "An API allows software components to communicate.",
})

MALFORMED_JSON = '{"status": "success",'

MISSING_FIELD_JSON = json.dumps({
    "status": "success",
})

WRONG_TYPE_JSON = json.dumps({
    "status": "success",
    "answer": 123,
})

WRONG_STATUS_JSON = json.dumps({
    "status": "failed",
    "answer": "The request failed.",
})

EXTRA_FIELD_JSON = json.dumps({
    "status": "success",
    "answer": "Hello",
    "unexpected": "extra field",
})

SURROUNDING_TEXT = (
    'Here is your answer: '
    '{"status":"success","answer":"Hello"}'
)

MESSAGES = [
    {
        "role": "user",
        "content": "Explain what an API is.",
    }
]


def fake_response(content):
    """Simulate an Ollama chat response without calling Ollama."""
    return SimpleNamespace(
        message=SimpleNamespace(content=content)
    )


# ==================================================
# CASE 1: Valid structured response
# ==================================================

def test_valid_structured_response():
    result = validate_response(VALID_JSON)

    assert isinstance(result, AIResponse)
    assert result.status == "success"
    assert result.answer != ""

    print("PASS: Valid JSON was parsed and validated.")


# ==================================================
# CASE 2: Malformed output
# ==================================================

def test_malformed_output():
    with pytest.raises(json.JSONDecodeError):
        validate_response(MALFORMED_JSON)

    print("PASS: Malformed JSON was rejected.")


# ==================================================
# CASE 3: Missing required field
# ==================================================

def test_missing_field():
    with pytest.raises(ValidationError):
        validate_response(MISSING_FIELD_JSON)

    print("PASS: Missing required field was rejected.")


# ==================================================
# CASE 4: Wrong type or invalid value
# ==================================================

def test_wrong_type():
    with pytest.raises(ValidationError):
        validate_response(WRONG_TYPE_JSON)

    print("PASS: Incorrect answer type was rejected.")


def test_wrong_status_value():
    with pytest.raises(ValidationError):
        validate_response(WRONG_STATUS_JSON)

    print("PASS: Unsupported status value was rejected.")


def test_unexpected_extra_field():
    with pytest.raises(ValidationError):
        validate_response(EXTRA_FIELD_JSON)

    print("PASS: Unexpected field was rejected.")


# ==================================================
# CASE 5: Extra surrounding text
# ==================================================

def test_extra_surrounding_text():
    with pytest.raises(json.JSONDecodeError):
        validate_response(SURROUNDING_TEXT)

    print("PASS: Surrounding text was rejected.")


# ==================================================
# CASE 6: Insufficient information
# ==================================================

def test_needs_clarification():
    clarification_json = json.dumps({
        "status": "needs_clarification",
        "answer": "Which employee policy are you asking about?",
    })

    result = validate_response(clarification_json)

    assert result.status == "needs_clarification"
    assert result.answer

    print("PASS: Clarification response passed validation.")


# ==================================================
# CASE 7A: Invalid output followed by successful retry
# ==================================================

def test_invalid_output_retries_and_recovers():
    client = Mock()

    client.chat.side_effect = [
        fake_response(MALFORMED_JSON),
        fake_response(VALID_JSON),
    ]

    result, error = generate_validated_response(
        client=client,
        model="test-model",
        messages=MESSAGES,
        max_attempts=2,
    )

    assert result is not None
    assert result.status == "success"
    assert error is None
    assert client.chat.call_count == 2

    print("PASS: Invalid output was retried and recovered.")


# ==================================================
# CASE 7B: Invalid output on every attempt
# ==================================================

def test_retry_exhaustion_returns_fallback():
    client = Mock()

    client.chat.side_effect = [
        fake_response(MALFORMED_JSON),
        fake_response(MISSING_FIELD_JSON),
    ]

    result, error = generate_validated_response(
        client=client,
        model="test-model",
        messages=MESSAGES,
        max_attempts=2,
    )

    assert result is None
    assert error is not None
    assert client.chat.call_count == 2

    print("PASS: Exhausted retries returned a failure result.")


# ==================================================
# CASE 7C: Timeout followed by successful retry
# ==================================================

def test_timeout_retries_and_recovers():
    client = Mock()

    client.chat.side_effect = [
        httpx.ReadTimeout("Simulated timeout"),
        fake_response(VALID_JSON),
    ]

    result, error = generate_validated_response(
        client=client,
        model="test-model",
        messages=MESSAGES,
        max_attempts=2,
    )

    assert result is not None
    assert error is None
    assert client.chat.call_count == 2

    print("PASS: Timeout was retried and recovered.")


# ==================================================
# CASE 7D: Timeout on every attempt
# ==================================================

def test_repeated_timeout_returns_fallback():
    client = Mock()

    client.chat.side_effect = [
        httpx.ReadTimeout("First simulated timeout"),
        httpx.ReadTimeout("Second simulated timeout"),
    ]

    result, error = generate_validated_response(
        client=client,
        model="test-model",
        messages=MESSAGES,
        max_attempts=2,
    )

    assert result is None
    assert error is not None
    assert client.chat.call_count == 2

    print("PASS: Repeated timeouts returned a failure result.")


# ==================================================
# Additional test: Respect maximum attempts
# ==================================================

def test_maximum_attempts_are_respected():
    client = Mock()
    client.chat.return_value = fake_response(MALFORMED_JSON)

    result, error = generate_validated_response(
        client=client,
        model="test-model",
        messages=MESSAGES,
        max_attempts=1,
    )

    assert result is None
    assert error is not None
    assert client.chat.call_count == 1

    print("PASS: Maximum attempt limit was respected.")