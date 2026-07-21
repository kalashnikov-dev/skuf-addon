"""
Точка входа ИИ-наблюдателя.

Важно: вызов Foundry долгий. Если делать его в обычном sync-хендлере «в лоб»,
на Windows иногда весь uvicorn перестаёт отвечать (даже /health).
Поэтому /events — async, а Azure зовём в отдельном потоке (asyncio.to_thread).
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

_SERVICE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_SERVICE_ROOT / ".env")

from app.azure_client import azure_configured  # noqa: E402
from app.bog_a import DEFAULT_MODEL, BogA  # noqa: E402
from app.foundry import strip_quotes  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observer")

app = FastAPI(title="Skuf Observer", version="0.4.1")

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

    if azure_configured():
        endpoint = strip_quotes(os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
        api_key = strip_quotes(os.getenv("AZURE_OPENAI_API_KEY") or "")
        deployment = strip_quotes(os.getenv("AZURE_OPENAI_DEPLOYMENT") or "")

        from openai import OpenAI

        # BogA.__init__ сначала ждёт ключ/модель; для Azure:
        # 1) создаём с валидным Gemini-ключом реестра (не используется),
        # 2) подменяем client + model_id на Foundry deployment.
        bog_arthur = BogA(
            model=DEFAULT_MODEL,
            api_key=api_key,
            cag_lines=150,
        )
        bog_arthur.client = OpenAI(
            base_url=endpoint,
            api_key=api_key,
            timeout=float(os.getenv("AZURE_HTTP_TIMEOUT", "45")),
            max_retries=0,
        )
        bog_arthur.set_model(deployment)
        logger.info("BogA: Azure/Foundry deployment=%s", deployment)
        print(f"[observer] BogA: Azure/Foundry deployment={deployment}", flush=True)

    elif os.getenv("GEMINI_API_KEY"):
        bog_arthur = BogA()
        logger.info("BogA: Configured to use Gemini")
        print("[observer] BogA: Configured to use Gemini", flush=True)

    else:
        logger.warning("BogA: NOT configured (no Azure or Gemini) — stub mode")
        print("[observer] BogA: NOT configured — stub mode", flush=True)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "azure_configured": azure_configured(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "boga_ready": bog_arthur is not None,
        "model_id": getattr(bog_arthur, "model_id", None) if bog_arthur else None,
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
        if first.type == "chat":
            print("[observer] stub chat: SKIP", flush=True)
            return EventsResponse(comment=None)
        stub = f"[заглушка] Видел: {first.player} -> {first.type}"
        print(f"[observer] stub: {stub}", flush=True)
        return EventsResponse(comment=stub)

    events_dicts = []
    for e in body.events:
        events_dicts.append(
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp,
                "player": e.player,
                "type": e.type,
                "payload": e.payload,
                "dimension": e.dimension,
                "pos": e.pos,
            }
        )

    try:
        comment = await asyncio.to_thread(
            bog_arthur.observe, events_dicts, body.online_players
        )
    except Exception as exc:
        logger.exception("BogA.observe failed: %s", type(exc).__name__)
        print(f"[observer] BogA.observe error: {exc}", flush=True)
        return EventsResponse(comment=None)

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
