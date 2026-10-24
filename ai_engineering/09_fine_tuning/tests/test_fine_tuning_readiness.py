import pytest

from src.fine_tuning_readiness import assess_readiness, readiness_template


def with_status(status):
    value = readiness_template()
    return {key: {"status": status, "reason": "Documented evidence"} for key in value}


def test_all_ready_is_ready():
    assert assess_readiness(with_status("READY"))["overall_status"] == "READY"


def test_one_not_ready_makes_overall_not_ready():
    value = with_status("READY")
    value["reviewed_dataset"] = {"status": "NOT_READY", "reason": "No dataset exists"}
    assert assess_readiness(value)["overall_status"] == "NOT_READY"


def test_review_items_make_overall_needs_review():
    assert assess_readiness(readiness_template())["overall_status"] == "NEEDS_REVIEW"


def test_missing_check_is_rejected():
    value = readiness_template()
    del value["evaluation"]
    with pytest.raises(ValueError, match="missing checks"):
        assess_readiness(value)

