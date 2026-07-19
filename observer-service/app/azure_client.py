"""
Вызов модели через Microsoft Foundry (Azure AI).

Рабочий паттерн (как в консольке):
  OpenAI(base_url="https://....services.ai.azure.com/api/projects/.../openai/v1", api_key=...)
  model = имя deployment (например gpt-5-mini)
"""

from __future__ import annotations

import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from openai import OpenAI

logger = logging.getLogger("observer.azure")

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "observer_system.md"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def azure_configured() -> bool:
    return bool(
        os.getenv("AZURE_OPENAI_ENDPOINT")
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    endpoint = _strip_quotes(os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
    api_key = _strip_quotes(os.getenv("AZURE_OPENAI_API_KEY") or "")
    # Не ретраим по 3 раза — иначе один «тупящий» Azure съедает минуту и мод ловит timeout.
    timeout_sec = float(os.getenv("AZURE_HTTP_TIMEOUT", "40"))
    logger.info("Foundry OpenAI base_url: %s (timeout=%ss, retries=0)", endpoint, timeout_sec)
    return OpenAI(
        base_url=endpoint,
        api_key=api_key,
        timeout=timeout_sec,
        max_retries=0,
    )


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def build_user_message(online_players: list[str], events_summary: str) -> str:
    online = ", ".join(online_players) if online_players else "(никого)"
    return (
        f"Сейчас онлайн: {online}\n\n"
        f"События:\n{events_summary}\n\n"
        "Если среди событий есть type=chat — это обращение к тебе: ответь на message игрока.\n"
        "Иначе — короткий комментарий к событию.\n"
        "Одна-две фразы для чата, без префикса имени."
    )


def format_events_for_prompt(events: list[Any]) -> str:
    lines: list[str] = []
    for ev in events:
        extra = ""
        if ev.payload:
            bits = [f"{k}={v}" for k, v in ev.payload.items()]
            extra = " | " + ", ".join(bits)
        where = ""
        if ev.dimension:
            where += f" dim={ev.dimension}"
        if ev.pos:
            where += f" pos={ev.pos}"
        lines.append(f"- {ev.player}: {ev.type}{extra}{where}")
    return "\n".join(lines)


def generate_comment(online_players: list[str], events: list[Any]) -> str | None:
    if not azure_configured():
        return None

    deployment = _strip_quotes(os.getenv("AZURE_OPENAI_DEPLOYMENT") or "")
    user_msg = build_user_message(online_players, format_events_for_prompt(events))

    # gpt-5-mini тратит completion-токены и на «внутренние» рассуждения.
    # Слишком маленький лимит (типа 120) → часто пустой content после долгого ожидания.
    # В рабочей консольке у тебя было 1500 — ставим разумный дефолт выше.
    max_tokens = int(os.getenv("AZURE_MAX_TOKENS", "800"))

    try:
        client = _client()
        kwargs: dict[str, Any] = {
            "model": deployment,
            "messages": [
                {"role": "system", "content": load_system_prompt()},
                {"role": "user", "content": user_msg},
            ],
            "max_completion_tokens": max_tokens,
        }

        temp_raw = os.getenv("AZURE_TEMPERATURE")
        if temp_raw is not None and temp_raw.strip() != "":
            kwargs["temperature"] = float(temp_raw)

        logger.info("Calling Foundry deployment=%s max_completion_tokens=%s", deployment, max_tokens)
        print(f"[observer] Calling Foundry ({deployment})...", flush=True)
        started = time.perf_counter()
        response = client.chat.completions.create(**kwargs)
        elapsed = time.perf_counter() - started
        logger.info("Foundry responded in %.1fs", elapsed)
        print(f"[observer] Foundry responded in {elapsed:.1f}s", flush=True)

        choice = response.choices[0]
        text = choice.message.content
        if not text:
            logger.warning(
                "Empty content (finish_reason=%s). Try raising AZURE_MAX_TOKENS in .env. raw=%s",
                getattr(choice, "finish_reason", None),
                response.model_dump(),
            )
            return None

        if response.usage:
            logger.info(
                "Azure usage: prompt=%s completion=%s total=%s",
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.total_tokens,
            )

        return text.strip()
    except Exception as exc:
        logger.exception(
            "Foundry chat completion failed (%s).",
            type(exc).__name__,
        )
        return None
