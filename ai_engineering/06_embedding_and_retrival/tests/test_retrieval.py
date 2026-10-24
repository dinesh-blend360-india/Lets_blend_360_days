import numpy as np
import pytest
from src.retrieval.similarity import cosine_similarity, top_k

def test_cosine_ranks_closest_vector_first():
    query, vectors = np.array([1.0, 0.0]), np.array([[0.9, 0.1], [0.0, 1.0]])
    assert top_k(query, vectors, 1)[0][0] == 0
    assert cosine_similarity(query, vectors)[0] > cosine_similarity(query, vectors)[1]

def test_rejects_invalid_top_k():
    with pytest.raises(ValueError): top_k(np.array([1.0]), np.array([[1.0]]), 0)

def test_rejects_dimension_mismatch():
    with pytest.raises(ValueError): cosine_similarity(np.array([1.0]), np.array([[1.0, 0.0]]))
