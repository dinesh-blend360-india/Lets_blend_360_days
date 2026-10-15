import pytest

from rag.answer_generator import GroundedAnswer, INSUFFICIENT_ANSWER
from rag.citation_validator import CitationValidationError, validate_citations
from rag.context_builder import build_context
from rag.pipeline import run_rag


def retrieved(chunk_id="chunk_a", text="Known fact", **metadata):
    return {"rank": metadata.pop("rank", 1), "similarity": metadata.pop("similarity", 0.9),
            "chunk_id": chunk_id, "text": text, "metadata": metadata}


def evidence_for(*results):
    return build_context("question", list(results)).evidence


def test_valid_citation_maps_from_evidence_metadata():
    evidence = evidence_for(retrieved(source="policy.md", heading_path="Rules", page=3))
    output = validate_citations(
        {"answer": "Known fact", "insufficient_evidence": False, "citations": ["chunk_a"]},
        evidence,
        retrieved_count=1,
        retrieval_results=[retrieved(source="policy.md", heading_path="Rules", page=3)],
        include_debug=True,
    )
    assert output["citations"] == [{"chunk_id": "chunk_a", "source": "policy.md", "heading_path": "Rules", "page": 3}]
    assert output["sources"] == ["chunk_a"]
    assert output["debug"]["retrieved"][0]["similarity"] == 0.9


def test_unknown_and_malformed_citations_are_rejected():
    evidence = evidence_for(retrieved())
    with pytest.raises(CitationValidationError, match="Unknown citation ID"):
        validate_citations({"answer": "x", "insufficient_evidence": False, "citations": ["unknown"]}, evidence, retrieved_count=1)
    with pytest.raises(CitationValidationError, match="non-empty string"):
        validate_citations({"answer": "x", "insufficient_evidence": False, "citations": [None]}, evidence, retrieved_count=1)


def test_duplicate_citations_are_deduplicated():
    evidence = evidence_for(retrieved())
    output = validate_citations({"answer": "x", "insufficient_evidence": False, "citations": ["chunk_a", "chunk_a"]}, evidence, retrieved_count=1)
    assert output["sources"] == ["chunk_a"]
    assert len(output["citations"]) == 1


def test_missing_supported_citation_is_rejected():
    evidence = evidence_for(retrieved())
    with pytest.raises(CitationValidationError, match="require at least one"):
        validate_citations({"answer": "x", "insufficient_evidence": False, "citations": []}, evidence, retrieved_count=1)


def test_model_source_mapping_is_ignored_in_favor_of_original_evidence():
    evidence = evidence_for(retrieved(source="original.md", heading_path="Original"))
    output = validate_citations({"answer": "x", "insufficient_evidence": False, "citations": ["chunk_a"], "source": "invented.md"}, evidence, retrieved_count=1)
    assert output["citations"][0]["source"] == "original.md"


def test_insufficient_response_has_empty_citations():
    evidence = evidence_for(retrieved())
    output = validate_citations({"answer": INSUFFICIENT_ANSWER, "insufficient_evidence": True, "citations": []}, evidence, retrieved_count=1)
    assert output["insufficient_evidence"] is True
    assert output["citations"] == []
    assert output["sources"] == []


def test_pipeline_orchestrates_and_returns_debug_without_document_text():
    calls = {}

    def fake_retriever(question, **kwargs):
        calls["retriever"] = (question, kwargs)
        return [retrieved(source="policy.md", heading_path="Rules", page=2)]

    def fake_generator(question, context, allowed_ids, **kwargs):
        calls["generator"] = (question, context, allowed_ids)
        return GroundedAnswer("Known fact", False, ["chunk_a"], "fake")

    output = run_rag("What is known?", retriever=fake_retriever, generator=fake_generator, include_debug=True)
    assert output["sources"] == ["chunk_a"]
    assert output["debug"]["retrieved_count"] == 1
    assert output["debug"]["used_chunk_ids"] == ["chunk_a"]
    assert "Known fact" not in output["debug"]
    assert calls["generator"][2] == ["chunk_a"]


def test_pipeline_empty_retrieval_abstains_without_generation():
    called = False

    def fake_generator(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("generator should not be called")

    output = run_rag("Unknown?", retriever=lambda *args, **kwargs: [], generator=fake_generator, include_debug=True)
    assert output["answer"] == INSUFFICIENT_ANSWER
    assert output["citations"] == []
    assert output["debug"]["retrieved_count"] == 0
    assert called is False


def test_pipeline_rejects_malformed_generator_response():
    with pytest.raises(CitationValidationError):
        run_rag("Question", retriever=lambda *args, **kwargs: [retrieved()], generator=lambda *args, **kwargs: {"answer": "x"})
