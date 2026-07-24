"""Отправка текста в игровой чат: RCON (быстро) или HTTP-эндпоинт мода."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("observer.chat_send")


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def send_chat_backend() -> str:
    """rcon | mod | none"""
    return (_env("SEND_CHAT_BACKEND", "rcon") or "rcon").lower()


def _rcon_send_sync(text: str, prefix: str) -> dict[str, Any]:
    host = _env("RCON_HOST", "host.docker.internal")
    port = int(_env("RCON_PORT", "25575") or "25575")
    password = _env("RCON_PASSWORD")
    if not password:
        return {"ok": False, "error": "RCON_PASSWORD not set"}

    payload = text.strip()
    if len(payload.encode("utf-8")) > 1400:
        payload = payload[:400] + "…"

    component = {"text": f"<{prefix}> {payload}"}
    cmd = f"tellraw @a {json.dumps(component, ensure_ascii=False)}"

    try:
        from mcrcon import MCRcon
    except ImportError:
        return {"ok": False, "error": "mcrcon not installed"}

    try:
        with MCRcon(host, password, port=port) as mcr:
            resp = mcr.command(cmd)
        return {"ok": True, "backend": "rcon", "response": resp or ""}
    except Exception as exc:
        logger.exception("RCON send failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


async def _mod_send(text: str, prefix: str, *, trigger_boga: bool = True) -> dict[str, Any]:
    url = _env("MOD_CHAT_URL", "http://host.docker.internal:8081/broadcast")
    api_key = _env("MOD_CHAT_API_KEY") or _env("DEBUG_API_KEY")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {
        "text": text.strip(),
        "prefix": prefix,
        "triggerBoga": trigger_boga,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(url, json=body, headers=headers)
        if r.status_code >= 300:
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        return {"ok": True, "backend": "mod", "response": r.text[:200]}
    except Exception as exc:
        logger.exception("Mod chat send failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


async def _maybe_trigger_boga(text: str, send_result: dict[str, Any]) -> dict[str, Any]:
    """После отправки в чат — опционально дать Бог А шанс ответить (путь RCON)."""
    if not send_result.get("ok"):
        return send_result
    if send_chat_backend() == "mod":
        # Мод сам шлёт chat-событие в /events после broadcast.
        return send_result
    if (_env("SEND_CHAT_TRIGGER_BOGA", "true") or "true").lower() not in {"1", "true", "yes", "on"}:
        return send_result

    try:
        from app.main import talk_to_boga

        player = _env("SEND_CHAT_PREFIX", "Claude") or "Claude"
        result = await talk_to_boga(text, persist=True, player=player)
        reply = result.get("reply")
        if reply:
            boga_prefix = _env("BOGA_CHAT_PREFIX", "Бог А") or "Бог А"
            boga_send = await send_to_game_chat_raw(reply, prefix=boga_prefix, trigger_boga=False)
            send_result = {**send_result, "boga_reply": reply, "boga_send": boga_send}
        else:
            send_result = {**send_result, "boga_reply": None}
    except Exception as exc:
        logger.exception("SEND_CHAT_TRIGGER_BOGA failed")
        send_result = {**send_result, "boga_error": f"{type(exc).__name__}: {exc}"}
    return send_result


async def send_to_game_chat_raw(
    text: str,
    *,
    prefix: str | None = None,
    trigger_boga: bool = True,
) -> dict[str, Any]:
    """Отправка без рекурсивного Python-side trigger Boga (для ответов Бог А)."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty text"}

    backend = send_chat_backend()
    if backend == "none":
        return {"ok": False, "error": "SEND_CHAT_BACKEND=none"}

    use_prefix = prefix if prefix is not None else (_env("SEND_CHAT_PREFIX", "Claude") or "Claude")

    if backend == "mod":
        return await _mod_send(text, use_prefix, trigger_boga=trigger_boga)
    return await asyncio.to_thread(_rcon_send_sync, text, use_prefix)


async def send_to_game_chat(text: str) -> dict[str, Any]:
    result = await send_to_game_chat_raw(text)
    return await _maybe_trigger_boga(text, result)
