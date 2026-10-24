"""Validate reference decision cards and learner submissions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import (
    DECISION_CARD_OPTIONAL_FIELDS, DECISION_CARD_REQUIRED_FIELDS,
    SUBMISSION_OPTIONAL_FIELDS, SUBMISSION_REQUIRED_FIELDS,
    reject_unknown_fields, require_architecture, require_fields, require_object,
)


def validate_decision_card(card: Any) -> dict[str, Any]:
    value = require_object(card, "Decision card")
    require_fields(value, DECISION_CARD_REQUIRED_FIELDS, "Decision card")
    reject_unknown_fields(value, DECISION_CARD_REQUIRED_FIELDS | DECISION_CARD_OPTIONAL_FIELDS, "Decision card")
    require_architecture(value["chosen_approach"], "chosen_approach")
    require_architecture(value["rejected_alternative"], "rejected_alternative")
    if value["chosen_approach"] == value["rejected_alternative"]:
        raise ValueError("rejected_alternative must differ from chosen_approach")
    if value["scenario_id"] == "S06" and not value.get("staged_approach"):
        raise ValueError("S06 decision card requires staged_approach")
    if value["scenario_id"] == "S08" and value["chosen_approach"] != "DECISION_DEFERRED":
        raise ValueError("S08 must use DECISION_DEFERRED until essential discovery is complete")
    return value


def load_reference_cards(path: str | Path) -> list[dict[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError("Reference cards must be a non-empty JSON array")
    seen: set[str] = set()
    cards = []
    for item in value:
        card = validate_decision_card(item)
        if card["scenario_id"] in seen:
            raise ValueError(f"Duplicate reference card: {card['scenario_id']}")
        seen.add(card["scenario_id"])
        cards.append(card)
    return cards


def validate_submission(submission: Any) -> dict[str, Any]:
    value = require_object(submission, "Submission")
    require_fields(value, SUBMISSION_REQUIRED_FIELDS, "Submission")
    reject_unknown_fields(value, SUBMISSION_REQUIRED_FIELDS | SUBMISSION_OPTIONAL_FIELDS, "Submission")
    require_architecture(value["selected_architecture"], "selected_architecture")
    require_architecture(value["rejected_alternative"], "rejected_alternative")
    if value["selected_architecture"] == value["rejected_alternative"]:
        raise ValueError("rejected_alternative must differ from selected_architecture")
    if value["scenario_id"] == "S08" and value["selected_architecture"] != "DECISION_DEFERRED":
        raise ValueError("S08 requires DECISION_DEFERRED, not a guessed architecture")
    if value["scenario_id"] == "S06" and not value.get("staged_approach"):
        raise ValueError("S06 submission requires staged_approach")
    return value


def load_submission(path: str | Path) -> dict[str, Any]:
    return validate_submission(json.loads(Path(path).read_text(encoding="utf-8")))

