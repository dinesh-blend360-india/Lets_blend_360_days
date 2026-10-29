"""Compare two result files case by case.

Both files must come from the same suite with the same settings, so the only
difference is the one thing being tested. The comparison is keyed by case ID
and reports regressions separately from fixes, because a net count can hide a
case that got worse.

    python -m obs.compare_runs outputs/before.jsonl outputs/after.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["id"]: row for row in rows}


def failed_checks(row: dict[str, Any]) -> set[str]:
    return {name for name, passed in (row.get("checks") or {}).items() if not passed}


def compare(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> dict[str, Any]:
    shared = sorted(set(before) & set(after))
    rows: list[dict[str, Any]] = []
    for case_id in shared:
        was, now = failed_checks(before[case_id]), failed_checks(after[case_id])
        if was == now:
            verdict = "unchanged_pass" if not was else "unchanged_fail"
        elif not now:
            verdict = "fixed"
        elif not was:
            verdict = "regressed"
        else:
            verdict = "changed"
        rows.append(
            {
                "id": case_id,
                "verdict": verdict,
                "before_failed": sorted(was),
                "after_failed": sorted(now),
                "before_ms": (before[case_id].get("trace") or {}).get("total_ms"),
                "after_ms": (after[case_id].get("trace") or {}).get("total_ms"),
                "before_steps": (before[case_id].get("trace") or {}).get("step_count"),
                "after_steps": (after[case_id].get("trace") or {}).get("step_count"),
            }
        )
    return {
        "only_in_before": sorted(set(before) - set(after)),
        "only_in_after": sorted(set(after) - set(before)),
        "cases": rows,
        "totals": {
            "compared": len(rows),
            "fixed": sum(row["verdict"] == "fixed" for row in rows),
            "regressed": sum(row["verdict"] == "regressed" for row in rows),
            "changed": sum(row["verdict"] == "changed" for row in rows),
            "unchanged_fail": sum(row["verdict"] == "unchanged_fail" for row in rows),
            "unchanged_pass": sum(row["verdict"] == "unchanged_pass" for row in rows),
        },
    }


def render(report: dict[str, Any], *, only_changed: bool = False) -> str:
    lines = [f"{'case':<10}{'verdict':<16}{'before failed':<28}{'after failed':<28}{'ms before':>10}{'ms after':>10}"]
    lines.append("-" * 102)
    for row in report["cases"]:
        if only_changed and row["verdict"].startswith("unchanged"):
            continue
        lines.append(
            f"{row['id']:<10}{row['verdict']:<16}"
            f"{','.join(row['before_failed']) or '-':<28}"
            f"{','.join(row['after_failed']) or '-':<28}"
            f"{str(row['before_ms']):>10}{str(row['after_ms']):>10}"
        )
    totals = report["totals"]
    lines.append("")
    lines.append(
        f"compared={totals['compared']}  fixed={totals['fixed']}  regressed={totals['regressed']}  "
        f"changed={totals['changed']}  still-failing={totals['unchanged_fail']}  passing-throughout={totals['unchanged_pass']}"
    )
    if report["only_in_before"] or report["only_in_after"]:
        lines.append(
            f"WARNING: case sets differ. only_in_before={report['only_in_before']} only_in_after={report['only_in_after']}"
        )
    if totals["regressed"]:
        lines.append("WARNING: at least one case regressed; see the rows marked 'regressed'.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--only-changed", action="store_true", help="Hide cases whose checks did not change")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Emit the report as JSON")
    args = parser.parse_args()
    report = compare(load(args.before), load(args.after))
    print(json.dumps(report, indent=2) if args.as_json else render(report, only_changed=args.only_changed))


if __name__ == "__main__":
    main()
