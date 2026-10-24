"""Write immutable run artifacts and human-readable summaries."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def write_reports(output_dir: str | Path, results: list[dict[str, Any]], manifest: dict[str, Any], *, run_id: str | None = None) -> Path:
    root = Path(output_dir)
    run_id = run_id or new_run_id()
    run_dir = root / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"Run already exists and will not be overwritten: {run_dir}")
    run_dir.mkdir(parents=True)
    (root / "summaries").mkdir(parents=True, exist_ok=True)
    (root / "failure_analysis").mkdir(parents=True, exist_ok=True)
    payload = {"run_id": run_id, "manifest": manifest, "results": results}
    (run_dir / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_csv(run_dir / "results.csv", results)
    summary = render_summary(run_id, results, manifest)
    (run_dir / "summary.md").write_text(summary, encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "summaries" / "latest_summary.md").write_text(summary, encoding="utf-8")
    (root / "failure_analysis" / "failure_analysis.md").write_text(render_failures(run_id, results), encoding="utf-8")
    return run_dir


def _write_csv(path: Path, results: list[dict[str, Any]]) -> None:
    fields = ["case_id", "question", "corpus_precondition", "status", "primary_failure_stage", "retrieved_ids", "context_ids", "answer", "insufficient_evidence", "citation_ids"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in results:
            writer.writerow({field: json.dumps(item.get(field), ensure_ascii=False) if isinstance(item.get(field), (list, dict)) else item.get(field) for field in fields})


def render_summary(run_id: str, results: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    counts = {status: sum(item["status"] == status for item in results) for status in ("PASS", "FAIL", "BLOCKED_MISSING_SOURCE", "SKIPPED_RUNTIME_UNAVAILABLE", "NEEDS_MANUAL_REVIEW")}
    lines = [f"# Day 08 evaluation summary — {run_id}", "", f"Cases evaluated: {len(results)}", ""]
    lines.extend(f"- {key}: {value}" for key, value in counts.items())
    lines += ["", "| Case | Corpus | Status | Primary stage |", "|---|---|---|---|"]
    lines.extend(f"| {item['case_id']} | {item['corpus_precondition']} | {item['status']} | {item.get('primary_failure_stage') or 'none'} |" for item in results)
    lines += ["", "Retrieval metrics are reported only for cases with verified chunk labels. Keyword checks do not prove semantic grounding; supported answers retain a manual-review flag.", ""]
    return "\n".join(lines)


def render_failures(run_id: str, results: list[dict[str, Any]]) -> str:
    lines = [f"# Failure analysis — {run_id}", ""]
    for item in results:
        if item["status"] == "PASS":
            continue
        lines += [f"## {item['case_id']}", "", f"- Status: `{item['status']}`", f"- Primary stage: `{item.get('primary_failure_stage') or 'none'}`", f"- Contributing stages: `{', '.join(item.get('contributing_failure_stages', [])) or 'none'}`", f"- Retrieved IDs: `{item.get('retrieved_ids', [])}`", f"- Context IDs: `{item.get('context_ids', [])}`", f"- Evidence: {item.get('diagnosis_evidence', 'See results.json.')}", ""]
    return "\n".join(lines)

