"""Optional Ollama judge, gated on blind human labels."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
VERDICTS = {"PASS", "FAIL", "UNSURE"}


def read_labels(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 8 or any(row.get("human_label") not in VERDICTS for row in rows):
        raise ValueError("At least eight blind human labels must be completed before running the judge")
    ids = [row.get("case_id", "").strip() for row in rows]
    valid_ids = {
        json.loads(line)["id"] for line in (ROOT / "golden_cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
    }
    if len(set(ids)) != len(ids) or not set(ids) <= valid_ids:
        raise ValueError("Human labels must use unique case IDs from the golden dataset")
    return {case_id: row["human_label"] for case_id, row in zip(ids, rows)}


def parse_verdict(raw: str) -> dict[str, str]:
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("verdict") not in VERDICTS:
        raise ValueError("Judge verdict must be PASS, FAIL, or UNSURE")
    reason = value.get("reason")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise ValueError("Judge reason must contain 1–500 characters")
    return {"verdict": value["verdict"], "reason": reason.strip()}


def judge_row(row: dict[str, Any], *, model: str, host: str) -> dict[str, str]:
    from ollama import Client

    evidence = [item["result"] for item in row["tool_activity"] if item["tool_name"] == "lookup_internal_knowledge"]
    rubric = (ROOT / "rubric.md").read_text(encoding="utf-8")
    prompt = json.dumps({
        "rubric": rubric, "question": row["input"], "expected": row["expected"],
        "retrieved_results": evidence, "answer": row["assistant_output"],
    }, ensure_ascii=False)
    response = Client(host=host, timeout=90).chat(
        model=model,
        messages=[
            {"role": "system", "content": "Apply only the supplied completeness rubric. Return JSON with verdict and short reason. Do not assume facts outside the supplied evidence."},
            {"role": "user", "content": prompt},
        ],
        format="json",
        options={"temperature": 0, "num_predict": 180},
        think=False,
    )
    return parse_verdict(response.message.content)


def run(model: str, host: str, labels_path: Path, output: Path) -> list[dict[str, Any]]:
    labels = read_labels(labels_path)
    rows = [json.loads(line) for line in (ROOT / "outputs" / "baseline_results.jsonl").read_text(encoding="utf-8").splitlines()]
    if len({row["id"] for row in rows} & labels.keys()) < 8:
        raise ValueError("Baseline results must contain at least eight labeled cases")
    comparisons = []
    for row in rows:
        if row["id"] not in labels:
            continue
        verdict = judge_row(row, model=model, host=host)
        comparisons.append({
            "id": row["id"], "criterion": "completeness", "human_label": labels[row["id"]],
            "judge_verdict": verdict["verdict"], "reason": verdict["reason"],
            "agreement": verdict["verdict"] == labels[row["id"]],
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(item) for item in comparisons) + "\n", encoding="utf-8")
    return comparisons


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--labels", type=Path, required=True, help="Completed blind human labels CSV")
    args = parser.parse_args()
    result = run(args.model, args.host, args.labels, ROOT / "outputs" / "judge_comparison.jsonl")
    print(f"{sum(item['agreement'] for item in result)}/{len(result)} judge verdicts agree with blind labels")
