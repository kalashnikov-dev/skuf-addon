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
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

_SERVICE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_SERVICE_ROOT / ".env")

from app.azure_client import azure_configured  # noqa: E402
from app.bog_a import DEFAULT_MODEL, BogA  # noqa: E402
from app.foundry import strip_quotes  # noqa: E402
from app.logbuf import get_log_lines, install_log_buffer  # noqa: E402
from app.rag import auto_extraction_enabled, extract_facts, get_pipeline, rag_status  # noqa: E402

import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observer")
install_log_buffer("observer", maxlen=500)


def _safe_print(*args, **kwargs) -> None:
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        msg = " ".join(str(a) for a in args)
        enc = sys.stdout.encoding or "utf-8"
        print(msg.encode(enc, errors="replace").decode(enc), **kwargs)

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


def _env_flag(name: str, default: str = "false") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


def debug_endpoints_enabled() -> bool:
    return _env_flag("DEBUG_ENDPOINTS", "false")


def mcp_enabled() -> bool:
    # MCP по умолчанию вместе с debug; можно включить отдельно.
    if _env_flag("MCP_ENABLED", "false"):
        return True
    return debug_endpoints_enabled()


def require_debug(
    authorization: str | None = Header(default=None),
    x_debug_key: str | None = Header(default=None, alias="X-Debug-Key"),
) -> None:
    """DEBUG_ENDPOINTS + опциональный shared secret (Bearer или X-Debug-Key)."""
    if not debug_endpoints_enabled():
        raise HTTPException(status_code=404, detail="Not found")
    expected = (os.getenv("DEBUG_API_KEY") or "").strip()
    if not expected:
        return
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_debug_key:
        token = x_debug_key.strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


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


class ChatRequest(BaseModel):
    message: str
    persist: bool = False
    player: str = "Claude"


class ChatResponse(BaseModel):
    reply: str | None


class SendChatRequest(BaseModel):
    text: str


def _generic_openai_configured() -> bool:
    base_url = strip_quotes(os.getenv("OPENAI_BASE_URL") or "")
    model = strip_quotes(os.getenv("OPENAI_MODEL") or "")
    return bool(base_url and model)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Startup: инициализируем Бог А и память."""
    global bog_arthur

    if _generic_openai_configured():
        base_url = strip_quotes(os.getenv("OPENAI_BASE_URL") or "").rstrip("/")
        api_key = strip_quotes(os.getenv("OPENAI_API_KEY") or "") or "sk-noauth"
        model_name = strip_quotes(os.getenv("OPENAI_MODEL") or "")
        timeout = float(os.getenv("OPENAI_HTTP_TIMEOUT", "45"))

        from openai import OpenAI

        bog_arthur = BogA(
            model=DEFAULT_MODEL,
            api_key=api_key,
            cag_lines=150,
        )
        bog_arthur.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=0,
        )
        bog_arthur.set_model(model_name)
        logger.info("BogA: Generic OpenAI base_url=%s model=%s", base_url, model_name)
        print(f"[observer] BogA: Generic OpenAI base_url={base_url} model={model_name}", flush=True)

    elif azure_configured():
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
        logger.warning("BogA: NOT configured (no generic OpenAI, Azure or Gemini) — stub mode")
        print("[observer] BogA: NOT configured — stub mode", flush=True)

    try:
        get_pipeline().startup()
        st = rag_status()
        logger.info("Memory: ready=%s facts=%s semantic=%s", st["memory_ready"], st["fact_count"], st["semantic_ready"])
        print(
            f"[observer] Memory ready={st['memory_ready']} facts={st['fact_count']} semantic={st['semantic_ready']}",
            flush=True,
        )
    except Exception as exc:
        logger.exception("Memory startup failed: %s", type(exc).__name__)
        print(f"[observer] Memory startup failed: {exc}", flush=True)

    logger.info(
        "Debug endpoints=%s MCP=%s send_chat=%s",
        debug_endpoints_enabled(),
        mcp_enabled(),
        (os.getenv("SEND_CHAT_BACKEND") or "rcon"),
    )
    yield


def _build_app() -> FastAPI:
    lifespan = app_lifespan
    mcp_app = None

    if mcp_enabled():
        try:
            from fastmcp.utilities.lifespan import combine_lifespans

            from app.mcp_server import mcp

            mcp_app = mcp.http_app(path="/")
            lifespan = combine_lifespans(app_lifespan, mcp_app.lifespan)
            logger.info("FastMCP enabled — will mount at /mcp")
        except Exception as exc:
            logger.exception("FastMCP init failed: %s", type(exc).__name__)
            print(f"[observer] FastMCP init failed: {exc}", flush=True)
            mcp_app = None
            lifespan = app_lifespan

    application = FastAPI(title="Skuf Observer", version="0.6.0", lifespan=lifespan)
    if mcp_app is not None:
        application.mount("/mcp", mcp_app)
        print("[observer] FastMCP mounted at /mcp", flush=True)
    return application


app = _build_app()


def _normalize_comment(comment: str | None) -> str | None:
    if not comment:
        return None
    comment_clean = comment.strip()
    if not comment_clean or comment_clean.upper() == "SKIP":
        return None
    return comment_clean


async def talk_to_boga(
    message: str,
    *,
    persist: bool = False,
    player: str = "Claude",
    online_players: list[str] | None = None,
) -> dict:
    """Прямой разговор с Бог А (используется /chat и MCP say_to_boga)."""
    message = (message or "").strip()
    if not message:
        return {"reply": None, "error": "empty message"}

    if bog_arthur is None:
        return {"reply": "[заглушка] Бог А не сконфигурирован", "error": "boga_not_ready"}

    synthetic = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "player": player or "Claude",
        "type": "chat",
        "payload": {"message": message},
        "dimension": None,
        "pos": None,
    }

    pipe = get_pipeline()
    memory_block = ""
    try:
        memory_block = pipe.build_context(message).block
    except Exception:
        logger.exception("build_context failed in talk_to_boga")

    try:
        comment = await asyncio.to_thread(
            bog_arthur.observe, [synthetic], online_players or [], memory_block or None
        )
    except Exception as exc:
        logger.exception("BogA.observe failed in talk_to_boga")
        return {"reply": None, "error": f"{type(exc).__name__}: {exc}"}

    reply = _normalize_comment(comment)
    if persist and reply:
        try:
            # remember_events ждёт объекты с attrs или dict — передаём GameEvent-like через dict path
            class _Ev:
                def __init__(self, d: dict):
                    self.player = d["player"]
                    self.type = d["type"]
                    self.payload = d.get("payload") or {}

            pipe.remember_events([_Ev(synthetic)])
            pipe.remember_observer_reply(reply)
        except Exception:
            logger.exception("persist failed in talk_to_boga")

    return {"reply": reply}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "generic_openai_configured": _generic_openai_configured(),
        "azure_configured": azure_configured(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "boga_ready": bog_arthur is not None,
        "model_id": getattr(bog_arthur, "model_id", None) if bog_arthur else None,
        "memory": rag_status(),
        "debug_endpoints": debug_endpoints_enabled(),
        "mcp_enabled": mcp_enabled(),
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


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_debug)])
async def chat_with_boga(body: ChatRequest):
    result = await talk_to_boga(body.message, persist=body.persist, player=body.player)
    if result.get("error") == "boga_not_ready":
        raise HTTPException(status_code=503, detail="BogA not configured")
    return ChatResponse(reply=result.get("reply"))


@app.get("/logs", dependencies=[Depends(require_debug)])
async def logs(limit: int = Query(default=100, ge=1, le=500)):
    lines = get_log_lines(limit)
    return {"lines": lines, "count": len(lines)}


@app.get("/logs/stream", dependencies=[Depends(require_debug)])
async def logs_stream(request: Request):
    """Простой SSE-хвост кольцевого буфера."""

    async def gen():
        last_len = 0
        while True:
            if await request.is_disconnected():
                break
            lines = get_log_lines(0)
            if len(lines) > last_len:
                for line in lines[last_len:]:
                    yield f"data: {line}\n\n"
                last_len = len(lines)
            elif len(lines) < last_len:
                # буфер ротировался
                last_len = 0
            await asyncio.sleep(1.0)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/send_chat", dependencies=[Depends(require_debug)])
async def send_chat_http(body: SendChatRequest):
    """REST-обёртка над send_to_game_chat (удобно без MCP)."""
    from app.chat_send import send_to_game_chat

    return await send_to_game_chat(body.text)


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

    chat_texts: list[str] = []
    for e in body.events:
        if e.type == "chat":
            msg = (e.payload or {}).get("message", "")
            if msg:
                chat_texts.append(msg)
                remembered = parse_memory_command(msg)
                if remembered:
                    added = pipe.remember_fact(remembered, player=e.player, origin="explicit")
                    print(f"[observer] remember_fact('{remembered[:60]}') added={added}", flush=True)

    query_text = " ".join(chat_texts) or " ".join(f"{e.player} {e.type}" for e in body.events)
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
        _safe_print(f"[observer] BogA.observe error: {exc}", flush=True)
        return EventsResponse(comment=None)

    try:
        pipe.remember_events(body.events)
    except Exception:
        logger.exception("remember_events failed")

    if chat_texts and auto_extraction_enabled() and bog_arthur is not None:
        client = getattr(bog_arthur, "client", None)
        model = getattr(bog_arthur, "model_id", None)
        for text in chat_texts:
            asyncio.create_task(_auto_extract(client, model, text))

    reply = _normalize_comment(comment)
    if reply:
        try:
            pipe.remember_observer_reply(reply)
        except Exception:
            logger.exception("remember_observer_reply failed")

        _safe_print(f"[observer] comment ok: {reply[:120]}", flush=True)
        return EventsResponse(comment=reply)

    _safe_print("[observer] BogA returned no comment; staying silent", flush=True)
    logger.warning("BogA returned no comment; staying silent")
    return EventsResponse(comment=None)


async def _auto_extract(client, model, text: str) -> None:
    """Фоновое извлечение фактов из одного chat-сообщения (best-effort)."""
    try:
        facts = await asyncio.to_thread(extract_facts, client, model, text)
        pipe = get_pipeline()
        for fact in facts:
            if pipe.remember_fact(fact, origin="auto"):
                _safe_print(f"[observer] auto-fact: {fact[:60]}", flush=True)
    except Exception:
        logger.exception("auto extract task failed")
