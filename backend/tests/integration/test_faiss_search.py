from app.services.search.embeddings import HashEmbeddingProvider


def test_hash_embedding_provider_is_lightweight_and_deterministic():
    provider = HashEmbeddingProvider()
    first = provider.embed(["pregnant woman"])[0]
    second = provider.embed(["pregnant woman"])[0]
    assert first == second
    assert len(first) == provider.dimension

