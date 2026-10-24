"""Create inspectable decision reports without overwriting history."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def render_report(result: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        f"# Architecture decision report — {result['scenario_id']}", "",
        f"- Selected: `{result['selected_architecture']}`",
        f"- Reference: `{result['reference_architecture']}`",
        f"- Architecture match: `{result['architecture_match']}`",
        f"- Score: **{result['score']}/{result['maximum_score']}**", "",
        "## Rubric", "", "| Dimension | Score | Maximum |", "|---|---:|---:|",
    ]
    lines.extend(f"| {name.replace('_', ' ').title()} | {item['score']} | {item['max']} |" for name, item in result["rubric"].items())
    card = result.get("reference_decision_card")
    if card:
        lines += [
            "", "## Reference decision card", "",
            f"- Business outcome: {card['business_outcome']}",
            f"- Problem type: {card['problem_type']}",
            f"- Knowledge/freshness: {card['knowledge_source']} / {card['knowledge_freshness']}",
            f"- Chosen approach: `{card['chosen_approach']}`",
            f"- Why: {card['why_this_approach']}",
            f"- Key risk: {card['key_risk']}",
            f"- Validation: {card['validation_plan']}",
        ]
    lines += ["", "## Missing requirements", ""]
    lines.extend(f"- {item}" for item in result["missing_requirements"] or ["None"])
    lines += ["", "## Suggested improvements", ""]
    lines.extend(f"- {item}" for item in result["suggested_improvements"] or ["None"])
    lines += ["", result["explanation"], ""]
    return "\n".join(lines)


def write_decision_report(output_dir: str | Path, result: dict[str, Any], manifest: dict[str, Any], *, run_id: str | None = None) -> Path:
    root = Path(output_dir)
    run_id = run_id or new_run_id()
    run_dir = root / "run_history" / run_id
    if run_dir.exists():
        raise FileExistsError(f"Run already exists and will not be overwritten: {run_dir}")
    run_dir.mkdir(parents=True)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    payload = {"run_id": run_id, "manifest": manifest, "result": result}
    (run_dir / "result.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = render_report(result, manifest)
    (run_dir / "report.md").write_text(report, encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (reports / "latest_report.md").write_text(report, encoding="utf-8")
    return run_dir

