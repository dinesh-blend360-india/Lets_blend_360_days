import numpy as np
from src.config import EmbeddingConfig
from src.embeddings.bge_provider import BGEProvider

class FakeModel:
    max_seq_length = 8
    tokenizer = None
    def get_sentence_embedding_dimension(self): return 3
    def encode(self, texts, **kwargs): return np.array([[len(text), 1, 0] for text in texts], dtype=np.float32)

def test_provider_normalizes_and_reports_dimension():
    provider = BGEProvider(EmbeddingConfig(use_query_instruction=False), model=FakeModel())
    vectors = provider.embed_documents(["abc", "abcd"])
    assert vectors.shape == (2, 3)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1)
    assert provider.dimension == 3
