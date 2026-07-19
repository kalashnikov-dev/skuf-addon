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

from app.azure_client import azure_configured, generate_comment  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observer")

app = FastAPI(title="Skuf Observer", version="0.3.0")


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
    if azure_configured():
        logger.info("Azure/Foundry: configured")
        print("[observer] Azure/Foundry: configured", flush=True)
    else:
        logger.warning("Azure/Foundry: NOT configured — stub mode")
        print("[observer] Azure/Foundry: NOT configured — stub mode", flush=True)


@app.get("/health")
async def health():
    # async = не ждёт Azure; всегда должен отвечать мгновенно
    return {
        "status": "ok",
        "azure_configured": azure_configured(),
    }


@app.post("/events", response_model=EventsResponse)
async def receive_events(body: EventsRequest):
    kinds = ", ".join(f"{e.player}:{e.type}" for e in body.events) or "(empty)"
    print(f"[observer] /events received: {kinds}", flush=True)
    logger.info("/events received: %s", kinds)

    if not body.events:
        return EventsResponse(comment=None)

    if not azure_configured():
        first = body.events[0]
        # В stub-режиме на chat не спамим — как SKIP
        if first.type == "chat":
            print("[observer] stub chat: SKIP", flush=True)
            return EventsResponse(comment=None)
        stub = f"[заглушка] Видел: {first.player} -> {first.type}"
        print(f"[observer] stub: {stub}", flush=True)
        return EventsResponse(comment=stub)

    # Azure в другом потоке → event loop свободен для /health
    comment = await asyncio.to_thread(generate_comment, body.online_players, body.events)
    if comment:
        print(f"[observer] comment ok: {comment[:120]}", flush=True)
        return EventsResponse(comment=comment)

    print("[observer] Azure returned no comment; staying silent", flush=True)
    logger.warning("Azure returned no comment; staying silent")
    return EventsResponse(comment=None)
