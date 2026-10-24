import pytest

from src.tool_schemas import (
    DESCRIPTION_MAX_LENGTH, TOOL_DEFINITIONS, ToolValidationError,
    validate_create_arguments, validate_lookup_arguments,
)


def test_exactly_two_tool_schemas_are_exposed():
    names = [item["function"]["name"] for item in TOOL_DEFINITIONS]
    assert names == ["lookup_internal_knowledge", "create_service_request"]
    assert all(item["function"]["parameters"]["additionalProperties"] is False for item in TOOL_DEFINITIONS)


@pytest.mark.parametrize("value", [
    {"query": ""}, {"query": "x", "top_k": 0}, {"query": "x", "top_k": 6},
    {"query": "x", "top_k": True}, {"query": "x", "unknown": 1},
    {"query": "x", "category": "secret"},
])
def test_invalid_lookup_arguments_are_rejected(value):
    with pytest.raises(ToolValidationError):
        validate_lookup_arguments(value)


@pytest.mark.parametrize("value", [
    {"description": "d", "priority": "normal"},
    {"title": "", "description": "d", "priority": "normal"},
    {"title": "t", "description": "d", "priority": "urgent"},
    {"title": "t", "description": "x" * (DESCRIPTION_MAX_LENGTH + 1), "priority": "normal"},
    {"title": "t", "description": "d", "priority": "normal", "actor": "admin"},
])
def test_invalid_action_arguments_are_rejected(value):
    with pytest.raises(ToolValidationError):
        validate_create_arguments(value)

