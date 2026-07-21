"""Сборка RAG-контекста и lifecycle pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.rag.ingest import ingest_knowledge
from app.rag.retriever import Retriever
from app.rag.session import SessionMemory
from app.rag.settings import embeddings_configured, get_rag_settings
from app.rag.store import QdrantStore

logger = logging.getLogger("observer.rag.pipeline")


@dataclass
class RagContext:
    enabled: bool
    block: str
    lore_hits: int
    memory_hits: int


class RagPipeline:
    def __init__(self) -> None:
        self.settings = get_rag_settings()
        self.store: QdrantStore | None = None
        self.session: SessionMemory | None = None
        self.retriever: Retriever | None = None
        self.ready = False
        self.last_error: str | None = None

    def startup(self) -> None:
        if not self.settings.enabled:
            logger.info("RAG disabled (RAG_ENABLED=false)")
            return
        if not embeddings_configured():
            self.last_error = "embeddings not configured"
            logger.warning("RAG enabled but embeddings not configured — running without RAG")
            return
        try:
            self.store = QdrantStore(self.settings)
            if not self.store.ping():
                self.last_error = "qdrant unreachable"
                logger.warning("Qdrant unreachable at %s", self.settings.qdrant_url)
                return
            self.store.ensure_collections()
            ingest_knowledge(
                self.store,
                self.settings,
                force=self.settings.reindex_on_startup,
            )
            self.session = SessionMemory(self.store, self.settings)
            self.retriever = Retriever(self.store, self.settings)
            self.ready = True
            self.last_error = None
            logger.info(
                "RAG ready (lore_points=%s)",
                self.store.collection_count(self.settings.lore_collection),
            )
        except Exception as exc:
            self.ready = False
            self.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("RAG startup failed")

    def build_context(self, query: str) -> RagContext:
        if not self.ready or self.retriever is None or self.session is None:
            # всё равно отдадим recent session если есть только память без qdrant — но без ready session is None
            return RagContext(enabled=False, block="", lore_hits=0, memory_hits=0)

        parts: list[str] = []
        lore_hits = 0
        memory_hits = 0
        try:
            result = self.retriever.retrieve(query)
            lore_hits = len(result.lore)
            memory_hits = len(result.memory)
            retrieved = result.as_prompt_block()
            if retrieved:
                parts.append(retrieved)
        except Exception:
            logger.exception("RAG retrieve failed")

        recent = self.session.as_prompt_block()
        if recent:
            parts.append(recent)

        observer_lines = self.session.recent_observer_lines(5)
        if observer_lines:
            joined = " | ".join(observer_lines)
            parts.append(
                "Твои недавние реплики (не повторяй формулировки и ритм):\n" + joined
            )

        return RagContext(
            enabled=True,
            block="\n\n".join(parts).strip(),
            lore_hits=lore_hits,
            memory_hits=memory_hits,
        )

    def remember_events(self, events: list[Any]) -> None:
        if not self.ready or self.session is None:
            return
        for ev in events:
            etype = getattr(ev, "type", "?")
            player = getattr(ev, "player", None)
            payload = getattr(ev, "payload", {}) or {}
            if etype == "chat":
                msg = payload.get("message", "")
                text = f"{player}: {msg}"
            else:
                bits = ", ".join(f"{k}={v}" for k, v in payload.items()) if payload else ""
                text = f"{player} → {etype}" + (f" ({bits})" if bits else "")
            # события в буфер всегда; в Qdrant — чтобы не раздувать на каждый join можно только chat/death
            persist = etype in {"chat", "death", "advancement", "dimension"}
            self.session.add(
                "event",
                text,
                player=player,
                event_type=etype,
                persist_vector=persist,
            )

    def remember_observer_reply(self, comment: str) -> None:
        if not self.ready or self.session is None:
            return
        self.session.add("observer", comment, persist_vector=True)


@lru_cache(maxsize=1)
def get_pipeline() -> RagPipeline:
    return RagPipeline()


def rag_status() -> dict:
    settings = get_rag_settings()
    pipe = get_pipeline()
    lore_points = 0
    memory_points = 0
    qdrant_ok = False
    if pipe.store is not None:
        qdrant_ok = pipe.store.ping()
        if qdrant_ok:
            lore_points = pipe.store.collection_count(settings.lore_collection)
            memory_points = pipe.store.collection_count(settings.memory_collection)
    return {
        "rag_enabled": settings.enabled,
        "rag_ready": pipe.ready,
        "embeddings_configured": embeddings_configured(),
        "qdrant_ok": qdrant_ok,
        "qdrant_url": settings.qdrant_url,
        "lore_points": lore_points,
        "memory_points": memory_points,
        "last_error": pipe.last_error,
    }
