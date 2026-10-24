from src.evaluation.evaluate_retrieval import _resolve_expected

def test_expected_text_is_resolved_to_chunk_id():
    records = [{"chunk_id": "c1", "text": "submit within 30 days", "metadata": {}}]
    expected, note = _resolve_expected({"expected_text_contains": ["30 days"]}, records)
    assert expected == {"c1"}
    assert note is None
