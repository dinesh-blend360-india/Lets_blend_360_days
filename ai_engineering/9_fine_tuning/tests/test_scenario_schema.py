import json

import pytest

from src.decision_validator import load_reference_cards
from src.scenario_loader import load_scenarios


def test_real_scenarios_and_references_are_complete():
    scenarios = load_scenarios()
    cards = load_reference_cards("data/reference_decision_cards.json")
    assert len(scenarios) == 8
    assert {item["scenario_id"] for item in scenarios} == {item["scenario_id"] for item in cards}
    assert next(item for item in scenarios if item["scenario_id"] == "S08")["reference_architecture"] == "DECISION_DEFERRED"


def test_missing_scenario_field_is_rejected(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps([{"scenario_id": "S01"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        load_scenarios(path)


def test_duplicate_scenario_id_is_rejected(tmp_path):
    scenario = load_scenarios()[0]
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps([scenario, scenario]), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate scenario_id"):
        load_scenarios(path)

