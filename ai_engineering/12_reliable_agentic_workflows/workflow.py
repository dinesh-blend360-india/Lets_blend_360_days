"""Deterministic leave workflow built from the Day 11 demo data."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4


DEFAULT_EMPLOYEES = {
    "E101": {"name": "Priya", "balance": 3},
    "E102": {"name": "Rahul", "balance": 0},
    "E103": {"name": "Anita", "balance": 5},
    "E104": {"name": "Sam", "balance": 2},
}
DEFAULT_FESTIVALS = {"Diwali": "2026-11-08", "Dussehra": "2026-10-20", "Pongal": "2027-01-14"}
STATES = {"received", "validated", "balance_checked", "approval_pending", "created", "eligible", "declined", "blocked", "failed"}
ALLOWED = {
    None: {"received"},
    "received": {"validated", "blocked", "failed"},
    "validated": {"balance_checked", "created", "blocked", "failed"},
    "balance_checked": {"blocked", "eligible", "approval_pending"},
    "approval_pending": {"created", "declined", "failed"},
}


class LeaveStore:
    """Local demo records; atomic replacement protects a completed single-process write."""

    def __init__(self, path: Path):
        self.path = path

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Store must contain a JSON list")
        for record in data:
            if not isinstance(record, dict) or not all(key in record for key in (
                "user_id", "date", "leave_days", "leave_type", "idempotency_key", "request_id",
            )):
                raise ValueError("Store contains an invalid leave record")
            if (not isinstance(record["user_id"], str)
                or not isinstance(record["date"], str)
                or isinstance(record["leave_days"], bool)
                or not isinstance(record["leave_days"], int)
                or not 1 <= record["leave_days"] <= 30
                or not isinstance(record["idempotency_key"], str)
                or not isinstance(record["request_id"], str)):
                raise ValueError("Store contains an invalid leave record")
            date.fromisoformat(record["date"])
        return data

    def create(self, record: dict[str, Any]) -> None:
        records = self.all()
        records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump(records, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.path)
        finally:
            tmp.unlink(missing_ok=True)


class LeaveWorkflow:
    def __init__(
        self, store: LeaveStore, log_path: Path,
        *, employees: dict[str, dict[str, Any]] | None = None,
        festivals: dict[str, str] | None = None,
        today: date | None = None,
    ):
        self.store = store
        self.log_path = log_path
        self.employees = employees if employees is not None else DEFAULT_EMPLOYEES
        self.festivals = festivals if festivals is not None else DEFAULT_FESTIVALS
        self.today = today or date.today()

    def run(
        self, *, user_id: str, festival: str, offset_days: int = 1,
        leave_days: int = 1, leave_type: str = "annual", create: bool = False,
        approve: Callable[[dict[str, Any]], bool] | None = None,
    ) -> dict[str, Any]:
        run_id = uuid4().hex
        trace: list[dict[str, Any]] = []

        def step(state: str, detail: str) -> None:
            previous = trace[-1]["state"] if trace else None
            if state not in ALLOWED.get(previous, set()):
                raise RuntimeError(f"Invalid state transition: {previous} -> {state}")
            trace.append({"state": state, "detail": detail})

        def finish(status: str, code: str, **fields: Any) -> dict[str, Any]:
            step(status, code)
            result = {"run_id": run_id, "status": status, "code": code, "trace": trace, **fields}
            try:
                self._audit(result)
            except OSError:
                result["audit_error"] = "AUDIT_WRITE_FAILED"
            return result

        step("received", "Input received")
        if not isinstance(user_id, str) or user_id not in self.employees:
            return finish("blocked", "UNKNOWN_USER")
        match = next((name for name in self.festivals if name.casefold() == str(festival).strip().casefold()), None)
        if match is None:
            return finish("blocked", "UNKNOWN_FESTIVAL")
        if isinstance(offset_days, bool) or not isinstance(offset_days, int) or not 0 <= offset_days <= 30:
            return finish("blocked", "INVALID_OFFSET")
        if isinstance(leave_days, bool) or not isinstance(leave_days, int) or not 1 <= leave_days <= 30:
            return finish("blocked", "INVALID_LEAVE_DAYS")
        if leave_type not in {"annual", "sick"}:
            return finish("blocked", "INVALID_LEAVE_TYPE")
        try:
            start = date.fromisoformat(self.festivals[match]) + timedelta(days=offset_days)
        except (TypeError, ValueError, OverflowError):
            return finish("failed", "INVALID_FESTIVAL_DATE")
        if start < self.today:
            return finish("blocked", "PAST_DATE", date=start.isoformat())
        step("validated", f"{match} + {offset_days} day(s) = {start.isoformat()}")
        key_text = f"{user_id}|{start.isoformat()}|{leave_type}|{leave_days}"
        key = hashlib.sha256(key_text.encode("utf-8")).hexdigest()[:20]
        try:
            records = self.store.all()
        except Exception:
            return finish("failed", "STORE_READ_FAILED")
        existing = next((record for record in records if record.get("idempotency_key") == key), None)
        if existing:
            return finish("created", "ALREADY_CREATED", date=start.isoformat(), request_id=existing["request_id"])
        end = start + timedelta(days=leave_days - 1)
        for record in records:
            if record["user_id"] != user_id:
                continue
            recorded_start = date.fromisoformat(record["date"])
            recorded_end = recorded_start + timedelta(days=record["leave_days"] - 1)
            if start <= recorded_end and recorded_start <= end:
                return finish("blocked", "OVERLAPPING_LEAVE", date=start.isoformat(), request_id=record["request_id"])
        used = sum(record["leave_days"] for record in records if record["user_id"] == user_id)
        available = int(self.employees[user_id]["balance"]) - used
        step("balance_checked", f"Trusted available balance: {available}; requested: {leave_days}")
        if available < leave_days:
            return finish("blocked", "INSUFFICIENT_BALANCE", date=start.isoformat(), available=available)
        if not create:
            return finish("eligible", "CHECK_ONLY", date=start.isoformat(), available=available)
        proposal = {"user_id": user_id, "date": start.isoformat(), "leave_days": leave_days, "leave_type": leave_type}
        step("approval_pending", "Awaiting approval for exact proposal")
        try:
            approved = bool(approve(proposal)) if approve is not None else False
        except Exception:
            return finish("failed", "APPROVAL_HANDLER_FAILED")
        if not approved:
            return finish("declined", "NOT_APPROVED", date=start.isoformat())
        record = {**proposal, "idempotency_key": key, "request_id": f"LR-{key[:10]}"}
        try:
            self.store.create(record)
        except Exception:
            return finish("failed", "STORE_WRITE_FAILED")
        return finish("created", "SIMULATED_CREATED", date=start.isoformat(), request_id=record["request_id"])

    def _audit(self, result: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result, default=str) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="E104")
    parser.add_argument("--festival", default="Diwali")
    parser.add_argument("--offset", type=int, default=1)
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--create", action="store_true", help="Propose a simulated local request")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent / "outputs"
    workflow = LeaveWorkflow(LeaveStore(base / "requests.json"), base / "runs.jsonl")

    def confirm(proposal: dict[str, Any]) -> bool:
        print("Simulated local leave proposal:", json.dumps(proposal))
        return input("Type CONFIRM to record it: ").strip() == "CONFIRM"

    print(json.dumps(workflow.run(
        user_id=args.user, festival=args.festival, offset_days=args.offset,
        leave_days=args.days, create=args.create, approve=confirm if args.create else None,
    ), indent=2))


if __name__ == "__main__":
    main()
