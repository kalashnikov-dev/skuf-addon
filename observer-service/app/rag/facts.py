"""Файловое хранилище фактов Бога А (always-on, не зависит от Qdrant).

Факты — это durable-знания о людях/мире, которые Бог А должен помнить между
рестартами: «запомни евген это кент из деревни». Хранятся в JSON рядом с
сервисом. При включённом Qdrant дополнительно дублируются вектором для
семантического поиска, но файл — источник правды.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger("observer.rag.facts")


@dataclass
class Fact:
    text: str
    origin: str = "explicit"  # explicit (команда «запомни») | auto (LLM-извлечение)
    subject: str | None = None
    source_player: str | None = None
    ts: float = 0.0


def _normalize(text: str) -> str:
    """Ключ для дедупа: нижний регистр, схлопнутые пробелы, без пунктуации по краям."""
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t.strip(" \t\n.,!?:;\"'«»()-")


class FactStore:
    """Список фактов в JSON-файле с дедупом и атомарной записью."""

    def __init__(self, path: Path, store=None, settings=None) -> None:
        self.path = Path(path)
        self.store = store          # опциональный QdrantStore для дублирования вектором
        self.settings = settings
        self._facts: list[Fact] = []
        self._keys: set[str] = set()
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to read facts file %s — starting empty", self.path)
            return
        for item in raw if isinstance(raw, list) else []:
            try:
                fact = Fact(**item)
            except TypeError:
                # старый/битый формат — пропускаем, но не падаем
                continue
            key = _normalize(fact.text)
            if key and key not in self._keys:
                self._facts.append(fact)
                self._keys.add(key)
        logger.info("Loaded %s facts from %s", len(self._facts), self.path)

    def _flush(self) -> None:
        """Атомарная запись всего списка (через временный файл + os.replace)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        data = [asdict(f) for f in self._facts]
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def remember(
        self,
        text: str,
        *,
        origin: str = "explicit",
        subject: str | None = None,
        player: str | None = None,
    ) -> bool:
        """Добавить факт. Возвращает True, если реально добавлен (не дубль)."""
        text = (text or "").strip()
        if not text:
            return False
        key = _normalize(text)
        if not key:
            return False
        with self._lock:
            if key in self._keys:
                return False
            fact = Fact(
                text=text,
                origin=origin,
                subject=subject,
                source_player=player,
                ts=time.time(),
            )
            self._facts.append(fact)
            self._keys.add(key)
            try:
                self._flush()
            except Exception:
                logger.exception("Failed to persist fact to %s", self.path)

        # Опционально — вектор в Qdrant (best-effort, файл уже сохранён)
        if self.store is not None:
            try:
                from app.rag.embeddings import embed_query

                vector = embed_query(text[:2000])
                self.store.upsert_memory(
                    text=text[:2000],
                    vector=vector,
                    role="fact",
                    player=player,
                    event_type=origin,
                )
            except Exception:
                logger.exception("Failed to upsert fact vector to Qdrant")
        return True

    def all(self) -> list[Fact]:
        with self._lock:
            return list(self._facts)

    def count(self) -> int:
        with self._lock:
            return len(self._facts)

    def as_prompt_block(self, query: str | None = None, limit: int | None = None) -> str:
        """Компактный блок фактов для инъекции в контекст. Пусто, если релевантных фактов нет."""
        facts = self.all()
        if not facts:
            return ""
        if query:
            tokens = set(re.findall(r"\w+", query.lower()))
            stop_words = {"как", "что", "где", "кто", "или", "это", "ты", "бог", "чем", "мне", "его", "нам", "все", "тут"}
            keywords = {t for t in tokens if len(t) > 2 and t not in stop_words}
            if keywords:
                matched = [
                    f for f in facts
                    if any(k in f.text.lower() for k in keywords)
                    or (f.source_player and f.source_player.lower() in keywords)
                ]
                facts = matched
            else:
                facts = []
        if not facts:
            return ""
        if limit is not None:
            facts = facts[-limit:]
        lines = ["Что ты уже знаешь (запомненные факты):"]
        for f in facts:
            who = f" (от {f.source_player})" if f.source_player else ""
            lines.append(f"- {f.text}{who}")
        return "\n".join(lines)
