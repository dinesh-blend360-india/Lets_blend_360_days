from src.metrics import mean_reciprocal_rank, recall_at_k, reciprocal_rank, retrieval_metrics


def test_recall_and_reciprocal_rank():
    retrieved = ["wrong", "relevant", "other"]
    assert recall_at_k(retrieved, ["relevant"], 1) == 0.0
    assert recall_at_k(retrieved, ["relevant"], 3) == 1.0
    assert reciprocal_rank(retrieved, ["relevant"]) == 0.5


def test_unlabelled_case_has_no_retrieval_metrics():
    values = retrieval_metrics(["a"], [])
    assert values["recall_at_5"] is None
    assert values["reciprocal_rank"] is None


def test_mrr_ignores_unlabelled_cases():
    records = [{"retrieval_metrics": {"reciprocal_rank": 1.0}}, {"retrieval_metrics": {"reciprocal_rank": None}}, {"retrieval_metrics": {"reciprocal_rank": 0.5}}]
    assert mean_reciprocal_rank(records) == 0.75

