from src.evidence_validator import classify_failure


OK = {"behavior_ok": True, "required_terms_present": True, "forbidden_terms_absent": True}


def classify(**overrides):
    values = dict(corpus_status="SUPPORTED_IN_CORPUS", error_stage=None, expected_ids=["right"], retrieved_ids=["right"], context_ids=["right"], answer_checks=OK, citation_valid=True)
    values.update(overrides)
    return classify_failure(**values)


def test_classifies_each_pipeline_stage():
    assert classify(corpus_status="MISSING_FROM_CORPUS")[0] == "CORPUS_COVERAGE"
    assert classify(retrieved_ids=[])[0] == "RETRIEVAL"
    assert classify(context_ids=[])[0] == "CONTEXT_CONSTRUCTION"
    assert classify(answer_checks={**OK, "required_terms_present": False})[0] == "GENERATION_GROUNDING"
    assert classify(citation_valid=False)[0] == "CITATION_MAPPING"
    assert classify(error_stage="RUNTIME_OR_CONFIGURATION")[0] == "RUNTIME_OR_CONFIGURATION"


def test_multi_part_evidence_requires_all_expected_chunks():
    primary, _ = classify(expected_ids=["manager", "business-unit"], retrieved_ids=["manager"], context_ids=["manager"])
    assert primary == "RETRIEVAL"


def test_retrieved_multi_part_evidence_missing_from_context_is_context_failure():
    primary, _ = classify(expected_ids=["manager", "business-unit"], retrieved_ids=["manager", "business-unit"], context_ids=["manager"])
    assert primary == "CONTEXT_CONSTRUCTION"

