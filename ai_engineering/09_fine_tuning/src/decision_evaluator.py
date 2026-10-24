"""Deterministically score architecture-decision submissions."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .decision_validator import load_reference_cards, load_submission
from .report_generator import write_decision_report
from .scenario_loader import DEFAULT_SCENARIOS, get_scenario


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_CARDS = PROJECT_DIR / "data" / "reference_decision_cards.json"


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    lowered = text.casefold()
    return [word for word in keywords if word.casefold() in lowered]


def _keyword_score(text: str, keywords: list[str], points: int) -> tuple[int, list[str]]:
    if not keywords:
        return points, []
    hits = _keyword_hits(text, keywords)
    return round(points * len(hits) / len(keywords)), hits


def evaluate_submission(submission: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    keywords = scenario["rubric_keywords"]
    selected = submission["selected_architecture"]
    reference = scenario["reference_architecture"]
    architecture_points = 25 if selected == reference else 0
    problem_points, problem_hits = _keyword_score(submission["reasoning"], keywords.get("problem", []), 15)
    requirement_points, requirement_hits = _keyword_score(submission["reasoning"], keywords.get("requirements", []), 15)

    rejected = submission["rejected_alternative"]
    rejected_points = 10 if rejected == scenario["rejected_alternative"] else 5 if rejected and rejected != selected else 0
    risk_points, risk_hits = _keyword_score(submission.get("key_risk", ""), keywords.get("risk", []), 10)
    discovery_points, discovery_hits = _keyword_score(submission["discovery_question"], keywords.get("discovery", []), 10)
    validation_points, validation_hits = _keyword_score(submission["validation_plan"], keywords.get("validation", []), 10)
    if scenario["scenario_id"] == "S06":
        staged_points, staged_hits = _keyword_score(submission.get("staged_approach", ""), keywords.get("staged", []), 5)
    else:
        staged_points, staged_hits = 5, []

    dimensions = {
        "architecture_alignment": {"score": architecture_points, "max": 25},
        "problem_identification": {"score": problem_points, "max": 15, "matched": problem_hits},
        "requirements_alignment": {"score": requirement_points, "max": 15, "matched": requirement_hits},
        "rejected_alternative": {"score": rejected_points, "max": 10},
        "key_risk": {"score": risk_points, "max": 10, "matched": risk_hits},
        "discovery_question": {"score": discovery_points, "max": 10, "matched": discovery_hits},
        "validation_plan": {"score": validation_points, "max": 10, "matched": validation_hits},
        "staged_approach": {"score": staged_points, "max": 5, "matched": staged_hits},
    }
    total = sum(item["score"] for item in dimensions.values())
    missing = [name for name, item in dimensions.items() if item["score"] < item["max"]]
    suggestions = []
    if architecture_points == 0:
        suggestions.append(f"Reconsider {selected}; the reference is {reference}, subject to its documented assumptions.")
    suggestions.extend(f"Strengthen {name.replace('_', ' ')} using scenario-specific requirements." for name in missing if name != "architecture_alignment")
    return {
        "scenario_id": scenario["scenario_id"],
        "selected_architecture": selected,
        "reference_architecture": reference,
        "architecture_match": selected == reference,
        "score": total,
        "maximum_score": 100,
        "rubric": dimensions,
        "missing_requirements": missing,
        "suggested_improvements": suggestions,
        "explanation": f"Deterministic rubric score {total}/100. Keyword matches are visible in each dimension; no LLM judge was used.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", required=True)
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS))
    parser.add_argument("--output-dir", default=str(PROJECT_DIR / "outputs"))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    submission = load_submission(args.submission)
    scenario = get_scenario(submission["scenario_id"], args.scenarios)
    result = evaluate_submission(submission, scenario)
    reference_cards = {item["scenario_id"]: item for item in load_reference_cards(DEFAULT_REFERENCE_CARDS)}
    result["reference_decision_card"] = reference_cards[submission["scenario_id"]]
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "submission": str(Path(args.submission).resolve()),
        "scenario_file": str(Path(args.scenarios).resolve()),
        "scoring": "deterministic rubric v1",
    }
    if args.no_write:
        print(json.dumps({"manifest": manifest, "result": result}, indent=2, ensure_ascii=False))
    else:
        output = write_decision_report(args.output_dir, result, manifest)
        print(output)


if __name__ == "__main__":
    main()

