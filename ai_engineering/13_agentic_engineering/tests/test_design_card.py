import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


root = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("day13_validator", root / "validate_card.py")
validator = module_from_spec(spec)
spec.loader.exec_module(validator)


def test_card_has_ten_stages_and_three_golden_cases():
    card = json.loads((root / "design_card.json").read_text(encoding="utf-8"))
    assert validator.validate(card) == []
    assert len(card["lifecycle"]) == 10
    assert len(card["golden_cases"]) >= 3


def test_validator_rejects_missing_handoff():
    card = json.loads((root / "design_card.json").read_text(encoding="utf-8"))
    card["lifecycle"][0]["handoff"] = ""
    assert validator.validate(card)
