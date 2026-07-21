"""Azure/Foundry embeddings через тот же OpenAI-compatible клиент."""

from __future__ import annotations

import logging
from typing import Sequence

from app.foundry import get_foundry_client
from app.rag.settings import get_rag_settings

logger = logging.getLogger("observer.rag.embeddings")


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Вернуть векторы той же длины, что texts. Пустой список → []."""
    cleaned = [t.strip() for t in texts if t and t.strip()]
    if not cleaned:
        return []

    settings = get_rag_settings()
    client = get_foundry_client()
    response = client.embeddings.create(
        model=settings.embedding_deployment,
        input=cleaned,
    )
    by_index = sorted(response.data, key=lambda d: d.index)
    vectors = [list(d.embedding) for d in by_index]
    if len(vectors) != len(cleaned):
        raise RuntimeError(
            f"embedding count mismatch: got {len(vectors)} expected {len(cleaned)}"
        )
    logger.debug(
        "Embedded %s texts via %s (dim=%s)",
        len(vectors),
        settings.embedding_deployment,
        len(vectors[0]) if vectors else 0,
    )
    return vectors


def embed_query(text: str) -> list[float]:
    vectors = embed_texts([text])
    if not vectors:
        raise ValueError("empty query for embedding")
    return vectors[0]
