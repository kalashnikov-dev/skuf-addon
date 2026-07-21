"""Общий клиент Microsoft Foundry (OpenAI-compatible)."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from openai import OpenAI

logger = logging.getLogger("observer.foundry")


def strip_quotes(value: str) -> str:
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
def get_foundry_client() -> OpenAI:
    endpoint = strip_quotes(os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
    api_key = strip_quotes(os.getenv("AZURE_OPENAI_API_KEY") or "")
    timeout_sec = float(os.getenv("AZURE_HTTP_TIMEOUT", "40"))
    logger.info("Foundry OpenAI base_url: %s (timeout=%ss, retries=0)", endpoint, timeout_sec)
    return OpenAI(
        base_url=endpoint,
        api_key=api_key,
        timeout=timeout_sec,
        max_retries=0,
    )
