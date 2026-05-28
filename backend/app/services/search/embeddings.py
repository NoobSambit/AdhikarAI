import hashlib
import math
import re
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
            values = [0.0] * self.dimension
            tokens = re.findall(r"[\w]+", text.lower())
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "big") % self.dimension
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                values[bucket] += sign
            if not tokens:
                digest = hashlib.sha256(text.encode("utf-8")).digest()
                for index in range(self.dimension):
                    values[index] = (digest[index % len(digest)] / 255.0) - 0.5
            norm = math.sqrt(sum(value * value for value in values)) or 1.0
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
