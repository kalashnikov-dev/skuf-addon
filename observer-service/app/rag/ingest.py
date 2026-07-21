"""Индексация knowledge/*.md в Qdrant."""

from __future__ import annotations

import logging

from app.rag.chunking import load_knowledge_chunks
from app.rag.embeddings import embed_texts
from app.rag.settings import RagSettings, get_rag_settings
from app.rag.store import QdrantStore

logger = logging.getLogger("observer.rag.ingest")


def ingest_knowledge(
    store: QdrantStore | None = None,
    settings: RagSettings | None = None,
    *,
    force: bool = False,
) -> dict:
    settings = settings or get_rag_settings()
    store = store or QdrantStore(settings)
    store.ensure_collections()

    existing = store.collection_count(settings.lore_collection)
    if existing > 0 and not force:
        logger.info("Lore collection already has %s points — skip ingest", existing)
        return {"status": "skipped", "lore_points": existing}

    chunks = load_knowledge_chunks(
        settings.knowledge_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    if not chunks:
        logger.warning("No knowledge chunks in %s", settings.knowledge_dir)
        return {"status": "empty", "lore_points": 0}

    if force and existing > 0:
        store.clear_lore()

    # batch embeddings
    batch_size = 16
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = embed_texts([c.text for c in batch])
        total += store.upsert_lore(batch, vectors)
        logger.info("Ingested lore batch %s–%s", i, i + len(batch))

    logger.info("Ingest complete: %s chunks from %s", total, settings.knowledge_dir)
    return {
        "status": "ok",
        "lore_points": store.collection_count(settings.lore_collection),
        "chunks_upserted": total,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from dotenv import load_dotenv
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(root / ".env")
    print(ingest_knowledge(force=True))
