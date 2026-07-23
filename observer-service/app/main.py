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
import re
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

_SERVICE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_SERVICE_ROOT / ".env")

from app.azure_client import azure_configured  # noqa: E402
from app.bog_a import DEFAULT_MODEL, BogA  # noqa: E402
from app.foundry import strip_quotes  # noqa: E402
from app.rag import auto_extraction_enabled, extract_facts, get_pipeline, rag_status  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observer")

bog_arthur = None

# «запомни X», «запомни: X», «запомни, что X» — ci. Группа 1 = что запоминать.
_REMEMBER_RE = re.compile(r"^\s*запомни\b[\s,:\-—]*(?:что\b[\s,]*)?(.*)$", re.IGNORECASE | re.DOTALL)


def parse_memory_command(text: str) -> str | None:
    """None — не команда «запомни». "" — команда без содержимого. Иначе — что запомнить."""
    if not text:
        return None
    m = _REMEMBER_RE.match(text.strip())
    if not m:
        return None
    return m.group(1).strip()


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: инициализируем Бог А и память."""
    global bog_arthur

    if azure_configured():
        endpoint = strip_quotes(os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
        api_key = strip_quotes(os.getenv("AZURE_OPENAI_API_KEY") or "")
        deployment = strip_quotes(os.getenv("AZURE_OPENAI_DEPLOYMENT") or "")

        from openai import OpenAI

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

    # Память: файловый слой всегда, семантический (Qdrant) — если поднят
    try:
        get_pipeline().startup()
        st = rag_status()
        logger.info("Memory: ready=%s facts=%s semantic=%s", st["memory_ready"], st["fact_count"], st["semantic_ready"])
        print(f"[observer] Memory ready={st['memory_ready']} facts={st['fact_count']} semantic={st['semantic_ready']}", flush=True)
    except Exception as exc:
        logger.exception("Memory startup failed: %s", type(exc).__name__)
        print(f"[observer] Memory startup failed: {exc}", flush=True)

    yield


app = FastAPI(title="Skuf Observer", version="0.5.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "azure_configured": azure_configured(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "boga_ready": bog_arthur is not None,
        "model_id": getattr(bog_arthur, "model_id", None) if bog_arthur else None,
        "memory": rag_status(),
    }


@app.get("/memory")
async def memory_dump(limit: int = 20):
    """Дебаг: что Бог А запомнил (факты) и последние реплики/события."""
    pipe = get_pipeline()
    facts = [
        {"text": f.text, "origin": f.origin, "player": f.source_player}
        for f in (pipe.facts.all() if pipe.facts else [])
    ]
    recent = [
        {"role": t.role, "player": t.player, "type": t.event_type, "text": t.text}
        for t in (pipe.session.recent(limit) if pipe.session else [])
    ]
    return {"facts": facts, "recent": recent, "status": rag_status()}


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

    pipe = get_pipeline()

    # 1) Детерминированная команда «запомни X» из chat-сообщений — гарантированная запись
    chat_texts: list[str] = []
    for e in body.events:
        if e.type == "chat":
            msg = (e.payload or {}).get("message", "")
            if msg:
                chat_texts.append(msg)
                remembered = parse_memory_command(msg)
                if remembered:  # непустое содержимое команды
                    added = pipe.remember_fact(remembered, player=e.player, origin="explicit")
                    print(f"[observer] remember_fact('{remembered[:60]}') added={added}", flush=True)

    # 2) Контекст памяти (факты всегда + rolling history + опц. семантика) → в хвост промпта
    query_text = " ".join(chat_texts) or " ".join(
        f"{e.player} {e.type}" for e in body.events
    )
    memory_block = ""
    try:
        memory_block = pipe.build_context(query_text).block
    except Exception:
        logger.exception("build_context failed — continuing without memory block")

    try:
        comment = await asyncio.to_thread(
            bog_arthur.observe, events_dicts, body.online_players, memory_block or None
        )
    except Exception as exc:
        logger.exception("BogA.observe failed: %s", type(exc).__name__)
        print(f"[observer] BogA.observe error: {exc}", flush=True)
        return EventsResponse(comment=None)

    # 3) Персист событий в rolling history (независимо от того, ответил ли Бог А)
    try:
        pipe.remember_events(body.events)
    except Exception:
        logger.exception("remember_events failed")

    # 4) Фоновое авто-извлечение фактов из чата (не блокирует ответ)
    if chat_texts and auto_extraction_enabled() and bog_arthur is not None:
        client = getattr(bog_arthur, "client", None)
        model = getattr(bog_arthur, "model_id", None)
        for text in chat_texts:
            asyncio.create_task(_auto_extract(client, model, text))

    if comment:
        comment_clean = comment.strip()
        if comment_clean.upper() == "SKIP" or not comment_clean:
            print("[observer] comment: SKIP", flush=True)
            return EventsResponse(comment=None)

        try:
            pipe.remember_observer_reply(comment_clean)
        except Exception:
            logger.exception("remember_observer_reply failed")

        print(f"[observer] comment ok: {comment_clean[:120]}", flush=True)
        return EventsResponse(comment=comment_clean)

    print("[observer] BogA returned no comment; staying silent", flush=True)
    logger.warning("BogA returned no comment; staying silent")
    return EventsResponse(comment=None)


async def _auto_extract(client, model, text: str) -> None:
    """Фоновое извлечение фактов из одного chat-сообщения (best-effort)."""
    try:
        facts = await asyncio.to_thread(extract_facts, client, model, text)
        pipe = get_pipeline()
        for fact in facts:
            if pipe.remember_fact(fact, origin="auto"):
                print(f"[observer] auto-fact: {fact[:60]}", flush=True)
    except Exception:
        logger.exception("auto extract task failed")
