"""Masking applied before any payload leaves the process.

Masking happens here, at the tracer boundary, so a value is already a
placeholder by the time it is written to a trace file or sent to LangSmith.
Hiding a value later in a UI would not protect the exported trace.
"""

from __future__ import annotations

import re
from typing import Any


# Each rule is (name, compiled pattern, replacement). Order matters: the API-key
# rule runs before the employee-ID rule so a key containing "E1023" is not
# partially rewritten first.
_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("api_key", re.compile(r"\b(?:sk|pk|lsv2_pt|lsv2_sk)[-_][A-Za-z0-9_-]{8,}\b"), "<redacted:api_key>"),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<masked:email>"),
    ("employee_id", re.compile(r"\bE\d{3,6}\b"), "<masked:employee_id>"),
    # The lookarounds reject digits embedded in a longer token. Without them
    # this rule rewrites the digit runs inside generated identifiers such as
    # "generated-7499265617abcd" and "SR-7499265617AB", which would corrupt the
    # call IDs and request IDs a trace is meant to be searchable by.
    ("phone_in", re.compile(r"(?<![\w-])(?:\+91[-\s]?)?[6-9]\d{9}(?![\w-])"), "<masked:phone>"),
]

# Keys whose value is dropped outright rather than pattern-matched. A secret
# does not become safe by being shortened, so these never reach a trace.
_DROP_KEYS = frozenset({"api_key", "authorization", "password", "token", "secret", "langsmith_api_key"})

MASK_PLACEHOLDERS = frozenset(
    {"<masked:email>", "<masked:employee_id>", "<masked:phone>", "<redacted:api_key>", "<dropped>"}
)


def mask_text(value: str) -> str:
    """Apply every rule to one string."""
    for _name, pattern, replacement in _RULES:
        value = pattern.sub(replacement, value)
    return value


def mask(value: Any) -> Any:
    """Recursively mask a JSON-shaped payload.

    Dict keys are preserved (they are field names, not data) but a key in
    _DROP_KEYS has its value replaced wholesale.
    """
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, dict):
        return {
            key: "<dropped>" if str(key).lower() in _DROP_KEYS else mask(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [mask(item) for item in value]
    return value


def find_unmasked(value: Any) -> list[str]:
    """Return any values a rule should have caught. Used by the tests as a
    self-check that masking ran before export, not as a security guarantee."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            for name, pattern, _replacement in _RULES:
                for hit in pattern.findall(node):
                    found.append(f"{name}:{hit}")
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(value)
    return found
