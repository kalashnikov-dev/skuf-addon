"""Настройки RAG из env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _strip(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RagSettings:
    enabled: bool
    qdrant_url: str
    lore_collection: str
    memory_collection: str
    embedding_deployment: str
    embedding_dims: int
    top_k_lore: int
    top_k_memory: int
    score_threshold: float
    session_recent: int
    chunk_size: int
    chunk_overlap: int
    reindex_on_startup: bool
    knowledge_dir: Path
    memory_dir: Path


@lru_cache(maxsize=1)
def get_rag_settings() -> RagSettings:
    service_root = Path(__file__).resolve().parent.parent.parent
    knowledge = Path(
        _strip(os.getenv("RAG_KNOWLEDGE_DIR"))
        or str(service_root / "knowledge")
    )
    memory = Path(
        _strip(os.getenv("MEMORY_DIR"))
        or str(service_root / "data")
    )
    return RagSettings(
        enabled=_bool("RAG_ENABLED", True),
        qdrant_url=_strip(os.getenv("QDRANT_URL")) or "http://127.0.0.1:6333",
        lore_collection=_strip(os.getenv("RAG_LORE_COLLECTION")) or "skuf_lore",
        memory_collection=_strip(os.getenv("RAG_MEMORY_COLLECTION")) or "skuf_memory",
        embedding_deployment=_strip(os.getenv("AZURE_EMBEDDING_DEPLOYMENT"))
        or "text-embedding-3-small",
        embedding_dims=int(os.getenv("RAG_EMBEDDING_DIMS", "1536")),
        top_k_lore=int(os.getenv("RAG_TOP_K_LORE", "5")),
        top_k_memory=int(os.getenv("RAG_TOP_K_MEMORY", "3")),
        score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.25")),
        session_recent=int(os.getenv("RAG_SESSION_RECENT", "12")),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
        reindex_on_startup=_bool("RAG_REINDEX_ON_STARTUP", False),
        knowledge_dir=knowledge,
        memory_dir=memory,
    )


def embeddings_configured() -> bool:
    """Нужны те же endpoint/key, что у чата, плюс deployment эмбеддингов."""
    return bool(
        _strip(os.getenv("AZURE_OPENAI_ENDPOINT"))
        and _strip(os.getenv("AZURE_OPENAI_API_KEY"))
        and get_rag_settings().embedding_deployment
    )
