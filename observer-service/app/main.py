"""
Точка входа ИИ-наблюдателя.

Важно: вызов Foundry долгий. Если делать его в обычном sync-хендлере «в лоб»,
на Windows иногда весь uvicorn перестаёт отвечать (даже /health).
Поэтому /events — async, а Azure зовём в отдельном потоке (asyncio.to_thread).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

_SERVICE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_SERVICE_ROOT / ".env")

from app.azure_client import azure_configured  # noqa: E402
from app.bog_a import BogA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observer")

app = FastAPI(title="Skuf Observer", version="0.3.0")

bog_arthur = None


class GameEvent(BaseModel):
    event_id: str = Field(description="Уникальный id, чтобы не обработать дважды")
    timestamp: float = Field(description="Когда случилось (unix time, секунды)")
    player: str = Field(description="Ник игрока")
    type: str = Field(description="Вид события: join, leave, death, chat, ...")
    payload: dict = Field(default_factory=dict)
    dimension: str | None = None
    pos: list[int] | None = None


class EventsRequest(BaseModel):
    events: list[GameEvent]
    online_players: list[str] = Field(default_factory=list)


class EventsResponse(BaseModel):
    comment: str | None


@app.on_event("startup")
def on_startup() -> None:
    global bog_arthur
    import os
    
    # 1. Check Azure configuration
    if azure_configured():
        endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip().rstrip("/")
        api_key = (os.getenv("AZURE_OPENAI_API_KEY") or "").strip()
        deployment = (os.getenv("AZURE_OPENAI_DEPLOYMENT") or "").strip()
        
        from openai import OpenAI
        bog_arthur = BogA(model=deployment, api_key=api_key)
        bog_arthur.client = OpenAI(base_url=endpoint, api_key=api_key)
        bog_arthur.model_id = deployment
        logger.info("BogA: Configured to use Azure GPT-5-mini")
        print("[observer] BogA: Configured to use Azure GPT-5-mini", flush=True)
        
    # 2. Check Gemini configuration
    elif os.getenv("GEMINI_API_KEY"):
        bog_arthur = BogA()
        logger.info("BogA: Configured to use Gemini")
        print("[observer] BogA: Configured to use Gemini", flush=True)
        
    else:
        logger.warning("BogA: NOT configured (no Azure or Gemini) — stub mode")
        print("[observer] BogA: NOT configured — stub mode", flush=True)


@app.get("/health")
async def health():
    import os
    return {
        "status": "ok",
        "azure_configured": azure_configured(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "boga_ready": bog_arthur is not None,
    }


@app.post("/events", response_model=EventsResponse)
async def receive_events(body: EventsRequest):
    kinds = ", ".join(f"{e.player}:{e.type}" for e in body.events) or "(empty)"
    print(f"[observer] /events received: {kinds}", flush=True)
    logger.info("/events received: %s", kinds)

    if not body.events:
        return EventsResponse(comment=None)

    if bog_arthur is None:
        first = body.events[0]
        # В stub-режиме на chat не спамим — как SKIP
        if first.type == "chat":
            print("[observer] stub chat: SKIP", flush=True)
            return EventsResponse(comment=None)
        stub = f"[заглушка] Видел: {first.player} -> {first.type}"
        print(f"[observer] stub: {stub}", flush=True)
        return EventsResponse(comment=stub)

    # Convert GameEvent objects to dicts for BogA
    events_dicts = []
    for e in body.events:
        events_dicts.append({
            "event_id": e.event_id,
            "timestamp": e.timestamp,
            "player": e.player,
            "type": e.type,
            "payload": e.payload,
            "dimension": e.dimension,
            "pos": e.pos
        })

    # Call observe in a separate thread to avoid blocking the event loop
    comment = await asyncio.to_thread(bog_arthur.observe, events_dicts, body.online_players)
    if comment:
        comment_clean = comment.strip()
        if comment_clean.upper() == "SKIP" or not comment_clean:
            print("[observer] comment: SKIP", flush=True)
            return EventsResponse(comment=None)
            
        print(f"[observer] comment ok: {comment_clean[:120]}", flush=True)
        return EventsResponse(comment=comment_clean)

    print("[observer] BogA returned no comment; staying silent", flush=True)
    logger.warning("BogA returned no comment; staying silent")
    return EventsResponse(comment=None)
