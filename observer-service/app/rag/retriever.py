"""Retrieval: lore + semantic session memory."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.rag.embeddings import embed_query
from app.rag.settings import RagSettings, get_rag_settings
from app.rag.store import QdrantStore

logger = logging.getLogger("observer.rag.retriever")


@dataclass
class RetrievalResult:
    lore: list[dict[str, Any]]
    memory: list[dict[str, Any]]
    query: str

    def as_prompt_block(self) -> str:
        parts: list[str] = []
        if self.lore:
            parts.append("Релевантные знания (RAG lore):")
            for i, hit in enumerate(self.lore, 1):
                title = hit.get("title") or hit.get("source") or "chunk"
                score = hit.get("score", 0.0)
                parts.append(f"{i}. ({title}, score={score:.2f})\n{hit.get('text', '').strip()}")
        if self.memory:
            parts.append("Похожие моменты из памяти сессии:")
            for i, hit in enumerate(self.memory, 1):
                role = hit.get("role") or "memory"
                score = hit.get("score", 0.0)
                parts.append(f"{i}. [{role}] score={score:.2f}\n{hit.get('text', '').strip()}")
        return "\n\n".join(parts).strip()


class Retriever:
    def __init__(
        self,
        store: QdrantStore,
        settings: RagSettings | None = None,
    ) -> None:
        self.store = store
        self.settings = settings or get_rag_settings()

    def retrieve(self, query: str) -> RetrievalResult:
        query = (query or "").strip()
        if not query:
            return RetrievalResult(lore=[], memory=[], query=query)

        vector = embed_query(query[:4000])
        lore = self.store.search(
            self.settings.lore_collection,
            vector,
            top_k=self.settings.top_k_lore,
            score_threshold=self.settings.score_threshold,
        )
        memory = self.store.search(
            self.settings.memory_collection,
            vector,
            top_k=self.settings.top_k_memory,
            score_threshold=self.settings.score_threshold,
        )
        logger.info(
            "RAG retrieve: lore=%s memory=%s query_len=%s",
            len(lore),
            len(memory),
            len(query),
        )
        return RetrievalResult(lore=lore, memory=memory, query=query)
