"""Короткая session memory (кольцевой буфер) + запись в Qdrant."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque

from app.rag.embeddings import embed_query
from app.rag.settings import RagSettings, get_rag_settings
from app.rag.store import QdrantStore

logger = logging.getLogger("observer.rag.session")


@dataclass(frozen=True)
class MemoryTurn:
    role: str  # player | observer | event
    text: str
    player: str | None = None
    event_type: str | None = None
    ts: float = 0.0


class SessionMemory:
    def __init__(
        self,
        store: QdrantStore | None = None,
        settings: RagSettings | None = None,
    ) -> None:
        self.settings = settings or get_rag_settings()
        self.store = store
        self._turns: Deque[MemoryTurn] = deque(maxlen=max(4, self.settings.session_recent * 2))
        self._lock = threading.Lock()

    def add(
        self,
        role: str,
        text: str,
        *,
        player: str | None = None,
        event_type: str | None = None,
        persist_vector: bool = True,
    ) -> None:
        text = (text or "").strip()
        if not text:
            return
        turn = MemoryTurn(
            role=role,
            text=text,
            player=player,
            event_type=event_type,
            ts=time.time(),
        )
        with self._lock:
            self._turns.append(turn)

        if persist_vector and self.store is not None:
            try:
                vector = embed_query(text[:2000])
                self.store.upsert_memory(
                    text=text[:2000],
                    vector=vector,
                    role=role,
                    player=player,
                    event_type=event_type,
                )
            except Exception:
                logger.exception("Failed to persist memory turn to Qdrant")

    def recent(self, n: int | None = None) -> list[MemoryTurn]:
        limit = n if n is not None else self.settings.session_recent
        with self._lock:
            items = list(self._turns)
        return items[-limit:]

    def recent_observer_lines(self, n: int = 5) -> list[str]:
        lines = [t.text for t in self.recent() if t.role == "observer"]
        return lines[-n:]

    def as_prompt_block(self) -> str:
        turns = self.recent()
        if not turns:
            return ""
        lines = ["Недавний контекст сессии (не повторяй свои старые формулировки):"]
        for t in turns:
            who = t.player or t.role
            if t.role == "observer":
                who = "Бог А"
            prefix = f"[{t.event_type}] " if t.event_type else ""
            lines.append(f"- {who}: {prefix}{t.text}")
        return "\n".join(lines)
