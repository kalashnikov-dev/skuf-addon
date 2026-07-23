"""Фоновое LLM-извлечение durable-фактов из сообщений чата.

Best-effort: любые ошибки глушим (память и ответ не должны страдать). Гейтится
env AUTO_FACT_EXTRACTION. Переиспользует клиент/модель уже поднятого BogA, чтобы
не плодить второй OpenAI-клиент.
"""

from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger("observer.rag.extract")

_EXTRACT_SYSTEM = (
    "Ты — модуль памяти. Из сообщения игрока в чате Minecraft вытащи только "
    "УСТОЙЧИВЫЕ факты о людях/мире, которые стоит помнить надолго (кто есть кто, "
    "прозвища, связи, роли). Игнорируй болтовню, эмоции, сиюминутное. "
    "Верни СТРОГО JSON-массив коротких строк-фактов на русском. "
    "Если запоминать нечего — верни []. Максимум 3 факта."
)


def auto_extraction_enabled() -> bool:
    raw = os.getenv("AUTO_FACT_EXTRACTION")
    if raw is None or raw.strip() == "":
        return True
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_facts(text: str) -> list[str]:
    """Достаёт JSON-массив строк из ответа модели (терпимо к обёрткам/мусору)."""
    if not text:
        return []
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    out: list[str] = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out[:3]


def extract_facts(client, model: str, chat_text: str) -> list[str]:
    """Вернуть список фактов из одного сообщения. При любой ошибке — []."""
    chat_text = (chat_text or "").strip()
    if not chat_text or client is None or not model:
        return []
    try:
        kwargs: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": _EXTRACT_SYSTEM},
                {"role": "user", "content": chat_text[:1000]},
            ],
        }
        mid = model.lower()
        if mid.startswith("gpt-5") or "gpt-5" in mid:
            kwargs["max_completion_tokens"] = 300
            effort = os.getenv("AZURE_REASONING_EFFORT", "minimal").strip()
            if effort:
                kwargs["reasoning_effort"] = effort
        else:
            kwargs["max_tokens"] = 200
            kwargs["temperature"] = 0.0
        resp = client.chat.completions.create(**kwargs)
        return _parse_facts(resp.choices[0].message.content or "")
    except Exception:
        logger.exception("Auto fact extraction failed")
        return []
