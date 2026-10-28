from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import pytest


path = Path(__file__).resolve().parents[1] / "workflow.py"
spec = spec_from_file_location("day12_workflow", path)
module = module_from_spec(spec)
spec.loader.exec_module(module)


def workflow(tmp_path, *, employees=None):
    return module.LeaveWorkflow(
        module.LeaveStore(tmp_path / "requests.json"), tmp_path / "runs.jsonl",
        employees=employees, today=date(2026, 10, 28),
    )


def test_exact_balance_and_idempotent_retries(tmp_path):
    app = workflow(tmp_path)
    answers = [app.run(user_id="E104", festival="Diwali", leave_days=2, create=True, approve=lambda _: True) for _ in range(10)]
    assert all(answer["status"] == "created" for answer in answers)
    assert answers[0]["code"] == "SIMULATED_CREATED"
    assert all(answer["code"] == "ALREADY_CREATED" for answer in answers[1:])
    assert len(app.store.all()) == 1
    assert len((tmp_path / "runs.jsonl").read_text(encoding="utf-8").splitlines()) == 10


def test_insufficient_balance_stays_blocked_across_ten_runs(tmp_path):
    app = workflow(tmp_path)
    results = [app.run(user_id="E104", festival="Diwali", leave_days=3, create=True, approve=lambda _: True) for _ in range(10)]
    assert {(item["status"], item["code"]) for item in results} == {("blocked", "INSUFFICIENT_BALANCE")}
    assert app.store.all() == []


def test_check_only_never_creates(tmp_path):
    app = workflow(tmp_path)
    result = app.run(user_id="E104", festival="Diwali", leave_days=2)
    assert result["status"] == "eligible"
    assert result["date"] == "2026-11-09"
    assert app.store.all() == []


def test_rejected_approval_and_bad_inputs(tmp_path):
    app = workflow(tmp_path)
    assert app.run(user_id="E104", festival="Diwali", create=True, approve=lambda _: False)["code"] == "NOT_APPROVED"
    assert app.run(user_id="E999", festival="Diwali")["code"] == "UNKNOWN_USER"
    assert app.run(user_id="E104", festival="Unknown")["code"] == "UNKNOWN_FESTIVAL"
    assert app.run(user_id="E104", festival="Dussehra")["code"] == "PAST_DATE"
    assert app.run(user_id="E104", festival="Diwali", offset_days=-1)["code"] == "INVALID_OFFSET"
    assert app.store.all() == []


def test_store_failure_is_not_reported_as_success(tmp_path):
    class FailingStore(module.LeaveStore):
        def create(self, record):
            raise OSError("simulated disk error")

    app = module.LeaveWorkflow(FailingStore(tmp_path / "requests.json"), tmp_path / "runs.jsonl", today=date(2026, 10, 28))
    result = app.run(user_id="E104", festival="Diwali", create=True, approve=lambda _: True)
    assert result["status"] == "failed"
    assert result["code"] == "STORE_WRITE_FAILED"


def test_approval_handler_failure_is_visible_and_has_no_side_effect(tmp_path):
    app = workflow(tmp_path)

    def broken(_proposal):
        raise RuntimeError("approval service down")

    result = app.run(user_id="E104", festival="Diwali", create=True, approve=broken)
    assert result["code"] == "APPROVAL_HANDLER_FAILED"
    assert app.store.all() == []


def test_overlapping_leave_is_blocked_even_when_start_or_length_changes(tmp_path):
    app = workflow(tmp_path, employees={"E104": {"name": "Sam", "balance": 5}})
    first = app.run(user_id="E104", festival="Diwali", leave_days=2, create=True, approve=lambda _: True)
    assert first["status"] == "created"
    for kwargs in ({"offset_days": 2}, {"leave_days": 1}):
        result = app.run(user_id="E104", festival="Diwali", create=True, approve=lambda _: True, **kwargs)
        assert result["code"] == "OVERLAPPING_LEAVE"
    assert len(app.store.all()) == 1


def test_corrupt_store_and_audit_error_are_visible(tmp_path):
    app = workflow(tmp_path)
    app.store.path.write_text('[{"user_id":"E104","leave_days":"bad"}]', encoding="utf-8")
    assert app.run(user_id="E104", festival="Diwali")["code"] == "STORE_READ_FAILED"
    app.store.path.unlink()
    app.log_path = tmp_path / "audit_directory"
    app.log_path.mkdir()
    result = app.run(user_id="E104", festival="Diwali", create=True, approve=lambda _: True)
    assert result["status"] == "created"
    assert result["audit_error"] == "AUDIT_WRITE_FAILED"
    assert len(app.store.all()) == 1


@pytest.mark.parametrize("kwargs,code", [
    ({"user_id": "E999", "festival": "Diwali"}, "UNKNOWN_USER"),
    ({"user_id": "E104", "festival": "Unknown"}, "UNKNOWN_FESTIVAL"),
    ({"user_id": "E104", "festival": "Dussehra"}, "PAST_DATE"),
    ({"user_id": "E104", "festival": "Diwali", "create": True, "approve": lambda _: False}, "NOT_APPROVED"),
])
def test_failure_decision_is_stable_across_ten_runs(tmp_path, kwargs, code):
    app = workflow(tmp_path)
    results = [app.run(**kwargs) for _ in range(10)]
    assert {item["code"] for item in results} == {code}
    assert app.store.all() == []
