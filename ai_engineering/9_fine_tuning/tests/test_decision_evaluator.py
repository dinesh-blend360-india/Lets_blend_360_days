import pytest

from src.decision_evaluator import evaluate_submission
from src.report_generator import write_decision_report
from src.scenario_loader import get_scenario


def test_transparent_rubric_scores_strong_s01_submission():
    scenario = get_scenario("S01")
    submission = {
        "scenario_id": "S01", "selected_architecture": "PROMPT_CONTEXT",
        "reasoning": "This is a format transformation best handled by a prompt and schema.",
        "rejected_alternative": "FINE_TUNING",
        "key_risk": "The model may omit a format field.",
        "discovery_question": "Which fields and quality threshold define success?",
        "validation_plan": "Test representative notes for schema validity.",
    }
    result = evaluate_submission(submission, scenario)
    assert result["architecture_match"] is True
    assert result["score"] == 100


def test_wrong_architecture_loses_alignment_points():
    scenario = get_scenario("S05")
    submission = {
        "scenario_id": "S05", "selected_architecture": "FINE_TUNING", "reasoning": "Use a model.",
        "rejected_alternative": "NO_LLM", "key_risk": "Wrong output",
        "discovery_question": "What inputs?", "validation_plan": "Test it."
    }
    result = evaluate_submission(submission, scenario)
    assert result["architecture_match"] is False
    assert result["rubric"]["architecture_alignment"]["score"] == 0


def test_report_generation_preserves_history(tmp_path):
    result = {"scenario_id": "S01", "selected_architecture": "PROMPT_CONTEXT", "reference_architecture": "PROMPT_CONTEXT", "architecture_match": True, "score": 100, "maximum_score": 100, "rubric": {}, "missing_requirements": [], "suggested_improvements": [], "explanation": "test"}
    first = write_decision_report(tmp_path, result, {"test": True}, run_id="fixed")
    assert (first / "result.json").is_file()
    assert (first / "report.md").is_file()
    assert (tmp_path / "reports" / "latest_report.md").is_file()
    with pytest.raises(FileExistsError):
        write_decision_report(tmp_path, result, {}, run_id="fixed")

