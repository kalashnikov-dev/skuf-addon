"""FastMCP tools: Claude ↔ observer / Minecraft chat."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger("observer.mcp")

mcp = FastMCP("skuf-observer")


def _debug_ok() -> bool:
    return (os.getenv("DEBUG_ENDPOINTS") or "").strip().lower() in {"1", "true", "yes", "on"}


@mcp.tool
def health() -> dict[str, Any]:
    """Статус observer / Бог А / память."""
    from app.azure_client import azure_configured
    from app.main import bog_arthur
    from app.rag import rag_status

    return {
        "status": "ok",
        "debug_endpoints": _debug_ok(),
        "azure_configured": azure_configured(),
        "boga_ready": bog_arthur is not None,
        "model_id": getattr(bog_arthur, "model_id", None) if bog_arthur else None,
        "memory": rag_status(),
        "ts": time.time(),
    }


@mcp.tool
def read_memory(limit: int = 20) -> dict[str, Any]:
    """Факты и недавние реплики/события из памяти Бог А."""
    from app.rag import get_pipeline

    pipe = get_pipeline()
    facts = [
        {"text": f.text, "origin": f.origin, "player": f.source_player}
        for f in (pipe.facts.all() if pipe.facts else [])
    ]
    recent = [
        {
            "role": t.role,
            "player": t.player,
            "type": t.event_type,
            "text": t.text,
            "ts": getattr(t, "ts", None),
        }
        for t in (pipe.session.recent(limit) if pipe.session else [])
    ]
    return {"facts": facts, "recent": recent}


@mcp.tool
def read_chat(limit: int = 30, since_id: str | None = None) -> dict[str, Any]:
    """
    Недавний чат/события из session memory.
    since_id — опционально пропустить записи до этого ts (строка float) или текста.
    """
    from app.rag import get_pipeline

    pipe = get_pipeline()
    turns = list(pipe.session.recent(max(limit, 50)) if pipe.session else [])
    items = []
    for t in turns:
        items.append(
            {
                "id": str(getattr(t, "ts", "")),
                "role": t.role,
                "player": t.player,
                "type": t.event_type,
                "text": t.text,
            }
        )
    if since_id:
        filtered = []
        seen = False
        for it in items:
            if seen:
                filtered.append(it)
            elif it["id"] == since_id or it["text"] == since_id:
                seen = True
        items = filtered if seen else items
    return {"messages": items[-limit:], "count": len(items[-limit:])}


@mcp.tool
async def say_to_boga(message: str, persist: bool = False) -> dict[str, Any]:
    """Прямой разговор с Бог А (мимо игрового чата)."""
    from app.main import talk_to_boga

    return await talk_to_boga(message, persist=persist)


@mcp.tool
async def send_chat(text: str) -> dict[str, Any]:
    """Написать в игровой чат (RCON или HTTP мода — см. SEND_CHAT_BACKEND)."""
    from app.chat_send import send_to_game_chat

    return await send_to_game_chat(text)


@mcp.tool
def read_logs(limit: int = 80) -> dict[str, Any]:
    """Последние строки логов observer."""
    from app.logbuf import get_log_lines

    lines = get_log_lines(limit)
    return {"lines": lines, "count": len(lines)}
