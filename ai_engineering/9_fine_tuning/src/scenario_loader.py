"""Load, inspect, and export templates for Day 09 scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .schemas import SCENARIO_OPTIONAL_FIELDS, SCENARIO_REQUIRED_FIELDS, reject_unknown_fields, require_architecture, require_fields, require_object


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = PROJECT_DIR / "data" / "architecture_scenarios.json"


def load_scenarios(path: str | Path = DEFAULT_SCENARIOS) -> list[dict[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ValueError("Scenario file must contain a non-empty JSON array")
    seen: set[str] = set()
    for index, item in enumerate(value):
        scenario = require_object(item, f"Scenario {index}")
        require_fields(scenario, SCENARIO_REQUIRED_FIELDS, f"Scenario {index}")
        reject_unknown_fields(scenario, SCENARIO_REQUIRED_FIELDS | SCENARIO_OPTIONAL_FIELDS, f"Scenario {index}")
        scenario_id = scenario["scenario_id"]
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError(f"Scenario {index} has an invalid scenario_id")
        if scenario_id in seen:
            raise ValueError(f"Duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
        require_architecture(scenario["reference_architecture"], f"{scenario_id}.reference_architecture")
        require_architecture(scenario["rejected_alternative"], f"{scenario_id}.rejected_alternative")
        if scenario_id == "S08" and scenario["reference_architecture"] != "DECISION_DEFERRED":
            raise ValueError("S08 must remain DECISION_DEFERRED until essential discovery is complete")
        if scenario_id == "S06" and not scenario.get("staged_approach"):
            raise ValueError("S06 must include a staged_approach")
        if not isinstance(scenario["rubric_keywords"], dict):
            raise ValueError(f"{scenario_id}.rubric_keywords must be an object")
    return value


def get_scenario(scenario_id: str, path: str | Path = DEFAULT_SCENARIOS) -> dict[str, Any]:
    for scenario in load_scenarios(path):
        if scenario["scenario_id"] == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def submission_template(scenario_id: str) -> dict[str, Any]:
    scenario = get_scenario(scenario_id)
    return {
        "scenario_id": scenario_id,
        "selected_architecture": "DECISION_DEFERRED" if scenario_id == "S08" else "",
        "reasoning": "",
        "rejected_alternative": "",
        "key_risk": "",
        "discovery_question": "",
        "validation_plan": "",
        "staged_approach": "" if scenario_id == "S06" else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List scenario IDs, titles, and references")
    group.add_argument("--show", metavar="SCENARIO_ID", help="Show one full scenario")
    group.add_argument("--export-template", metavar="SCENARIO_ID", help="Write a submission template")
    parser.add_argument("--output", help="Template destination; defaults to submissions/<ID>_submission.json")
    args = parser.parse_args()
    if args.list:
        for item in load_scenarios():
            print(f"{item['scenario_id']} | {item['reference_architecture']} | {item['title']}")
        return
    if args.show:
        print(json.dumps(get_scenario(args.show), indent=2, ensure_ascii=False))
        return
    template = submission_template(args.export_template)
    output = Path(args.output) if args.output else PROJECT_DIR / "submissions" / f"{args.export_template}_submission.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing submission: {output}")
    output.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

