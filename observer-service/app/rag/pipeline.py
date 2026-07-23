"""Сборка контекста памяти и lifecycle pipeline.

Два слоя:
  • Файловый (always-on): FactStore + персистентная SessionMemory. Работает без
    внешних сервисов, переживает рестарт. Это и есть базовая память Бога А.
  • Семантический (опциональный): Qdrant + embeddings. Включается, если поднят
    и сконфигурирован. Даёт семантический recall поверх файлового слоя.

Если семантический слой недоступен — файловый продолжает работать.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.rag.facts import FactStore
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
    fact_count: int


class RagPipeline:
    def __init__(self) -> None:
        self.settings = get_rag_settings()
        self.store: QdrantStore | None = None
        self.facts: FactStore | None = None
        self.session: SessionMemory | None = None
        self.retriever: Retriever | None = None
        self.ready = False            # файловый слой поднят
        self.semantic_ready = False   # Qdrant-слой поднят
        self.last_error: str | None = None

    def startup(self) -> None:
        # --- Файловый слой: всегда ---
        try:
            mem_dir = self.settings.memory_dir
            self.facts = FactStore(mem_dir / "facts.json")
            self.session = SessionMemory(persist_path=mem_dir / "history.json")
            self.ready = True
            logger.info(
                "Memory (file layer) ready: facts=%s dir=%s",
                self.facts.count(),
                mem_dir,
            )
        except Exception as exc:
            self.ready = False
            self.last_error = f"file layer: {type(exc).__name__}: {exc}"
            logger.exception("Memory file layer failed")
            return

        # --- Семантический слой: опционально ---
        if not self.settings.enabled:
            logger.info("Semantic RAG disabled (RAG_ENABLED=false) — file memory only")
            return
        if not embeddings_configured():
            logger.info("Embeddings not configured — file memory only")
            return
        try:
            store = QdrantStore(self.settings)
            if not store.ping():
                logger.warning("Qdrant unreachable at %s — file memory only", self.settings.qdrant_url)
                return
            store.ensure_collections()
            ingest_knowledge(store, self.settings, force=self.settings.reindex_on_startup)
            # Пересоздаём файловые слои с привязкой к store (вектор-дублирование)
            self.store = store
            self.facts = FactStore(self.settings.memory_dir / "facts.json", store=store, settings=self.settings)
            self.session = SessionMemory(
                store=store,
                settings=self.settings,
                persist_path=self.settings.memory_dir / "history.json",
            )
            self.retriever = Retriever(store, self.settings)
            self.semantic_ready = True
            self.last_error = None
            logger.info(
                "Semantic RAG ready (lore_points=%s)",
                store.collection_count(self.settings.lore_collection),
            )
        except Exception as exc:
            self.semantic_ready = False
            self.last_error = f"semantic layer: {type(exc).__name__}: {exc}"
            logger.exception("Semantic RAG startup failed — file memory still active")

    def build_context(self, query: str) -> RagContext:
        if not self.ready:
            return RagContext(enabled=False, block="", lore_hits=0, memory_hits=0, fact_count=0)

        parts: list[str] = []
        lore_hits = 0
        memory_hits = 0
        fact_count = 0

        # 1) Факты (всегда) — durable-знания
        if self.facts is not None:
            fact_count = self.facts.count()
            fact_block = self.facts.as_prompt_block()
            if fact_block:
                parts.append(fact_block)

        # 2) Семантический recall (только если Qdrant поднят)
        if self.semantic_ready and self.retriever is not None:
            try:
                result = self.retriever.retrieve(query)
                lore_hits = len(result.lore)
                memory_hits = len(result.memory)
                retrieved = result.as_prompt_block()
                if retrieved:
                    parts.append(retrieved)
            except Exception:
                logger.exception("RAG retrieve failed")

        # 3) Rolling история сессии (всегда) — непрерывность нити
        if self.session is not None:
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
            fact_count=fact_count,
        )

    def remember_fact(
        self,
        text: str,
        *,
        origin: str = "explicit",
        subject: str | None = None,
        player: str | None = None,
    ) -> bool:
        if not self.ready or self.facts is None:
            return False
        return self.facts.remember(text, origin=origin, subject=subject, player=player)

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
            # В Qdrant (если есть) кладём только «содержательные» события, чтобы не раздувать
            persist = self.semantic_ready and etype in {"chat", "death", "advancement", "dimension"}
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
        self.session.add("observer", comment, persist_vector=self.semantic_ready)


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
        "memory_ready": pipe.ready,
        "fact_count": pipe.facts.count() if pipe.facts else 0,
        "rag_enabled": settings.enabled,
        "semantic_ready": pipe.semantic_ready,
        "embeddings_configured": embeddings_configured(),
        "qdrant_ok": qdrant_ok,
        "qdrant_url": settings.qdrant_url,
        "lore_points": lore_points,
        "memory_points": memory_points,
        "last_error": pipe.last_error,
    }
