import json
from pathlib import Path

from obs.compare_runs import compare, load, render


def write(tmp_path: Path, name: str, rows: list[dict]) -> Path:
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def row(case_id: str, **checks) -> dict:
    return {"id": case_id, "checks": checks, "trace": {"total_ms": 1.0, "step_count": 5}}


def test_fixed_regressed_and_unchanged_are_distinguished(tmp_path):
    before = write(tmp_path, "b.jsonl", [
        row("A", source_citation=False),
        row("B", source_citation=True),
        row("C", source_citation=True),
        row("D", source_citation=False),
    ])
    after = write(tmp_path, "a.jsonl", [
        row("A", source_citation=True),
        row("B", source_citation=False),
        row("C", source_citation=True),
        row("D", source_citation=False),
    ])
    report = compare(load(before), load(after))
    verdicts = {item["id"]: item["verdict"] for item in report["cases"]}
    assert verdicts == {
        "A": "fixed", "B": "regressed", "C": "unchanged_pass", "D": "unchanged_fail",
    }
    assert report["totals"]["fixed"] == 1
    assert report["totals"]["regressed"] == 1


def test_a_case_failing_a_different_check_is_changed_not_fixed(tmp_path):
    before = write(tmp_path, "b.jsonl", [row("A", one=False, two=True)])
    after = write(tmp_path, "a.jsonl", [row("A", one=True, two=False)])
    report = compare(load(before), load(after))
    assert report["cases"][0]["verdict"] == "changed"
    assert report["totals"]["fixed"] == 0


def test_mismatched_case_sets_are_reported(tmp_path):
    before = write(tmp_path, "b.jsonl", [row("A", c=True), row("B", c=True)])
    after = write(tmp_path, "a.jsonl", [row("A", c=True), row("C", c=True)])
    report = compare(load(before), load(after))
    assert report["only_in_before"] == ["B"]
    assert report["only_in_after"] == ["C"]
    assert "case sets differ" in render(report)


def test_render_warns_on_regression(tmp_path):
    before = write(tmp_path, "b.jsonl", [row("A", c=True)])
    after = write(tmp_path, "a.jsonl", [row("A", c=False)])
    assert "regressed" in render(compare(load(before), load(after)))


def test_only_changed_hides_steady_cases(tmp_path):
    before = write(tmp_path, "b.jsonl", [row("A", c=True), row("B", c=False)])
    after = write(tmp_path, "a.jsonl", [row("A", c=True), row("B", c=True)])
    rendered = render(compare(load(before), load(after)), only_changed=True)
    assert "B" in rendered
    assert "\nA " not in rendered


def test_committed_before_after_evidence_shows_the_fix():
    """The checked-in Day 16 evidence must still show 8 fixed and 0 regressed."""
    evidence = Path(__file__).resolve().parents[1] / "evidence"
    report = compare(
        load(evidence / "before_flaky_retry0.jsonl"),
        load(evidence / "after_flaky_retry2.jsonl"),
    )
    assert report["totals"]["regressed"] == 0
    assert report["totals"]["fixed"] == 8
    assert report["totals"]["unchanged_fail"] == 0


def test_committed_no_fault_evidence_shows_the_fix_is_inert():
    evidence = Path(__file__).resolve().parents[1] / "evidence"
    report = compare(
        load(evidence / "before_nofault_retry0.jsonl"),
        load(evidence / "after_nofault_retry2.jsonl"),
    )
    assert report["totals"]["unchanged_pass"] == 22
    assert report["totals"]["fixed"] == 0
    assert report["totals"]["regressed"] == 0
