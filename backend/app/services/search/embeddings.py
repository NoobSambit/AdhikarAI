import hashlib
from abc import ABC, abstractmethod

from app.core.config import get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    dimension = 64

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values = [((digest[index % len(digest)] / 255.0) - 0.5) for index in range(self.dimension)]
            norm = sum(value * value for value in values) ** 0.5 or 1.0
            vectors.append([value / norm for value in values])
        return vectors


class SentenceTransformersProvider(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


def get_embedding_provider(lightweight: bool = False) -> EmbeddingProvider:
    settings = get_settings()
    if lightweight or settings.embedding_provider == "hash":
        return HashEmbeddingProvider()
    try:
        return SentenceTransformersProvider(settings.embedding_model)
    except Exception:
        return HashEmbeddingProvider()

