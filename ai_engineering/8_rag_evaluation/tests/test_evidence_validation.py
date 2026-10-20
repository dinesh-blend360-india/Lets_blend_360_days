from src.evidence_validator import context_evidence_ids, deterministic_answer_checks, validate_citation_ids


def test_context_and_citation_validation():
    context = {"evidence": [{"chunk_id": "a"}, {"chunk_id": "b"}]}
    assert context_evidence_ids(context) == ["a", "b"]
    assert validate_citation_ids(["a"], ["a", "b"])["valid"] is True
    invalid = validate_citation_ids(["invented"], ["a"])
    assert invalid == {"valid": False, "unknown_ids": ["invented"], "duplicate_ids": []}


def test_numeric_threshold_checks():
    case = {"must_include": ["500", "receipt"], "must_not_include": ["1000"], "expected_behavior": "ANSWER"}
    result = deterministic_answer_checks(case, "A receipt is required at 500 currency units or more.", False)
    assert result["behavior_ok"] is True
    assert result["required_terms_present"] is True
    assert result["forbidden_terms_absent"] is True


def test_unsupported_question_requires_abstention():
    case = {"must_include": ["Insufficient evidence"], "must_not_include": ["12 weeks"], "expected_behavior": "ABSTAIN"}
    result = deterministic_answer_checks(case, "Insufficient evidence in the provided documents to answer this question.", True)
    assert result["behavior_ok"] is True
    assert result["required_terms_present"] is True

