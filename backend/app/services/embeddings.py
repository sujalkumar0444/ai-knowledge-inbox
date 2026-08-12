"""
Embedding provider abstraction.

Two implementations behind one interface, selected via EMBEDDING_PROVIDER:

- LocalTfidfEmbedder (default): TF-IDF vectors via scikit-learn, refit over
  the full corpus on each ingestion/query. Zero network calls, zero cost,
  works instantly with no API key. Weaker than dense neural embeddings --
  it's a lexical/keyword-overlap signal, not a semantic one, so it will
  miss synonyms and paraphrases. That's the explicit tradeoff for
  "runs anywhere, no setup."

- OpenAIEmbedder: text-embedding-3-small via the OpenAI API. Real semantic
  embeddings, much better retrieval quality, but requires OPENAI_API_KEY
  and a network call per ingest/query.

Swapping providers is a one-line env var change (see .env.example) because
both implement the same `embed(texts) -> list[vector]` interface.
"""
from abc import ABC, abstractmethod

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    @abstractmethod
    def embed_query(self, text: str, corpus_texts: list[str]) -> list[float]:
        """
        Embed a single query.

        corpus_texts is provided because TF-IDF's vector space is defined by
        the corpus it was fit on -- the query must be embedded in that same
        fitted space. Dense embedders ignore this argument.
        """


class LocalTfidfEmbedder(EmbeddingProvider):
    """
    Refits a TF-IDF vectorizer over the full chunk corpus on every call.

    This is O(corpus size) per call, which is fine for a single-user demo
    app with a few hundred chunks and is exactly the kind of thing called
    out in README "what breaks at scale" -- a real deployment would use a
    persistent dense embedding index instead of refitting a sparse model
    on every request.
    """

    def _fit_vectorizer(self, corpus: list[str]) -> TfidfVectorizer:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=4096,
        )
        vectorizer.fit(corpus)
        return vectorizer

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectorizer = self._fit_vectorizer(texts)
        matrix = vectorizer.transform(texts)
        return matrix.toarray().tolist()

    def embed_query(self, text: str, corpus_texts: list[str]) -> list[float]:
        if not corpus_texts:
            return []
        vectorizer = self._fit_vectorizer(corpus_texts)
        vector = vectorizer.transform([text])
        return vector.toarray()[0].tolist()


class OpenAIEmbedder(EmbeddingProvider):
    def __init__(self) -> None:
        from openai import OpenAI  # local import: don't require the package/key unless used

        if not settings.openai_api_key:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Set it in .env or switch EMBEDDING_PROVIDER=local."
            )
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str, corpus_texts: list[str]) -> list[float]:
        return self.embed([text])[0]


_provider_instance: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    if settings.embedding_provider == "openai":
        _provider_instance = OpenAIEmbedder()
    else:
        _provider_instance = LocalTfidfEmbedder()

    logger.info(
        "Embedding provider initialized",
        extra={"extra_fields": {"provider": settings.embedding_provider}},
    )
    return _provider_instance


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    if va.size == 0 or vb.size == 0:
        return 0.0
    denom = (np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)
