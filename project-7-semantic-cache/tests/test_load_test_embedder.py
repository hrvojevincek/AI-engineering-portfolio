"""Load-test embedder tests."""

from src.cache.embed import EMBEDDING_DIMS
from src.cache.load_test_embedder import LoadTestEmbedder


def test_grouped_phrases_share_embedding():
    embedder = LoadTestEmbedder(
        [
            ["What is Python?", "Explain Python to me"],
            ["What is Redis?", "Explain Redis"],
        ]
    )
    first = embedder.embed("What is Python?")
    paraphrase = embedder.embed("Explain Python to me")
    unrelated = embedder.embed("What is Redis?")
    assert first == paraphrase
    assert first != unrelated
    assert len(first) == EMBEDDING_DIMS
