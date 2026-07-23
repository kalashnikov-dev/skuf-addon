"""Короткая session memory (кольцевой буфер) + запись в Qdrant."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
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
        persist_path: Path | str | None = None,
    ) -> None:
        self.settings = settings or get_rag_settings()
        self.store = store
        self.persist_path = Path(persist_path) if persist_path else None
        self._turns: Deque[MemoryTurn] = deque(maxlen=max(4, self.settings.session_recent * 2))
        self._lock = threading.Lock()
        if self.persist_path:
            self._load()

    def _load(self) -> None:
        if not self.persist_path or not self.persist_path.exists():
            return
        try:
            raw = json.loads(self.persist_path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to read history file %s — starting empty", self.persist_path)
            return
        for item in raw if isinstance(raw, list) else []:
            try:
                self._turns.append(MemoryTurn(**item))
            except TypeError:
                continue
        logger.info("Loaded %s history turns from %s", len(self._turns), self.persist_path)

    def _flush(self) -> None:
        """Атомарная запись окна истории (только под self._lock)."""
        if not self.persist_path:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.persist_path.with_suffix(self.persist_path.suffix + ".tmp")
        data = [asdict(t) for t in self._turns]
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.persist_path)

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
            if self.persist_path:
                try:
                    self._flush()
                except Exception:
                    logger.exception("Failed to persist history to %s", self.persist_path)

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
