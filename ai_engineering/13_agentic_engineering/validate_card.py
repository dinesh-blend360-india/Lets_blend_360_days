"""Validate the Day 13 design card's structure and evidence labels."""

import json
from pathlib import Path


STAGES = ["Discover", "Plan", "Build", "Verify & Review", "UAT", "Release", "Roll Out", "Run", "Monitor", "Improve"]
LABELS = {"EXISTING", "OBSERVED", "HYPOTHESIZED", "PROPOSED", "NEEDS VALIDATION"}


def validate(card: dict) -> list[str]:
    errors = []
    if [item.get("stage") for item in card.get("lifecycle", [])] != STAGES:
        errors.append("Lifecycle must contain the ten stages in order")
    for item in card.get("lifecycle", []):
        if item.get("label") not in LABELS or not all(item.get(key) for key in ("owner", "evidence", "handoff")):
            errors.append(f"Incomplete stage: {item.get('stage')}")
    cases = card.get("golden_cases", [])
    if len(cases) < 3 or len({item.get("id") for item in cases}) != len(cases):
        errors.append("At least three unique golden cases are required")
    for item in cases:
        if item.get("label") not in LABELS or not all(item.get(key) for key in ("input", "expected", "method")):
            errors.append(f"Incomplete golden case: {item.get('id')}")
    for key in ("current_prototype", "business_outcome", "architecture", "pilot_conditions", "alternative"):
        if card.get(key, {}).get("label") not in LABELS:
            errors.append(f"Missing evidence label: {key}")
    return errors


if __name__ == "__main__":
    path = Path(__file__).with_name("design_card.json")
    problems = validate(json.loads(path.read_text(encoding="utf-8")))
    if problems:
        raise SystemExit("\n".join(problems))
    print("Day 13 design card is structurally complete")
