"""Assess prerequisites for future fine-tuning without training a model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUSES = {"READY", "NOT_READY", "NEEDS_REVIEW"}
CHECKS = {
    "behavioral_problem": "A clearly defined persistent behavioral problem",
    "prompt_baseline": "A measured prompt-based baseline",
    "reviewed_dataset": "Representative reviewed input-output pairs",
    "data_splits": "Separate train, validation, and test sets",
    "data_quality": "Consistent, high-quality labels and examples",
    "sensitive_data": "Sensitive data removed or appropriately protected",
    "evaluation": "Evaluation criteria and regression tests",
    "base_model": "A suitable base model and supported tuning method",
    "cost_latency": "Cost and latency constraints understood",
    "deployment_maintenance": "Deployment, monitoring, rollback, and maintenance plan",
}


def readiness_template() -> dict[str, Any]:
    return {key: {"status": "NEEDS_REVIEW", "reason": "Document current evidence."} for key in CHECKS}


def assess_readiness(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Readiness input must be a JSON object")
    missing = sorted(set(CHECKS) - set(value))
    if missing:
        raise ValueError(f"Readiness input is missing checks: {missing}")
    items = []
    for check_id, description in CHECKS.items():
        item = value[check_id]
        if not isinstance(item, dict) or item.get("status") not in STATUSES or not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError(f"{check_id} requires a valid status and non-empty reason")
        items.append({"check_id": check_id, "description": description, "status": item["status"], "reason": item["reason"].strip()})
    statuses = {item["status"] for item in items}
    overall = "NOT_READY" if "NOT_READY" in statuses else "READY" if statuses == {"READY"} else "NEEDS_REVIEW"
    return {
        "overall_status": overall,
        "checks": items,
        "guidance": "Use retrieval for frequently changing private knowledge. Fine-tuning is mainly for persistent behavior, formatting, and task-specific patterns after a measured baseline.",
        "limitations": [
            "Fine-tuning does not guarantee factual accuracy.",
            "Fine-tuning does not keep changing knowledge current.",
            "Fine-tuning does not inherently provide source citations.",
            "This assessment does not train, deploy, or modify a model.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export-template")
    group.add_argument("--assess")
    args = parser.parse_args()
    if args.export_template:
        output = Path(args.export_template)
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite existing file: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(readiness_template(), indent=2) + "\n", encoding="utf-8")
        print(output)
        return
    value = json.loads(Path(args.assess).read_text(encoding="utf-8"))
    print(json.dumps(assess_readiness(value), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
