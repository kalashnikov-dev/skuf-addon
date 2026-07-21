"""Qdrant store: lore + memory collections."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.rag.chunking import TextChunk
from app.rag.settings import RagSettings, get_rag_settings

logger = logging.getLogger("observer.rag.store")


class QdrantStore:
    def __init__(self, settings: RagSettings | None = None) -> None:
        self.settings = settings or get_rag_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url, timeout=10)

    def ping(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception as exc:
            logger.warning("Qdrant ping failed: %s", exc)
            return False

    def ensure_collections(self) -> None:
        dim = self.settings.embedding_dims
        for name in (self.settings.lore_collection, self.settings.memory_collection):
            self._ensure_collection(name, dim)

    def _ensure_collection(self, name: str, dim: int) -> None:
        exists = self.client.collection_exists(name)
        if exists:
            info = self.client.get_collection(name)
            # vectors can be VectorParams or dict depending on version
            vectors = info.config.params.vectors
            current_dim = None
            if isinstance(vectors, qm.VectorParams):
                current_dim = vectors.size
            elif isinstance(vectors, dict) and "" in vectors:
                current_dim = vectors[""].size
            if current_dim is not None and current_dim != dim:
                logger.warning(
                    "Recreating collection %s: dim %s -> %s", name, current_dim, dim
                )
                self.client.delete_collection(name)
                exists = False
        if not exists:
            self.client.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
            )
            logger.info("Created Qdrant collection %s (dim=%s)", name, dim)

    def collection_count(self, name: str) -> int:
        try:
            return int(self.client.count(name, exact=True).count)
        except Exception:
            return 0

    def upsert_lore(self, chunks: list[TextChunk], vectors: list[list[float]]) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(vectors):
            raise ValueError("chunks/vectors length mismatch")
        points = [
            qm.PointStruct(
                id=self._point_id(c.chunk_id),
                vector=vectors[i],
                payload={
                    "text": c.text,
                    "source": c.source,
                    "title": c.title,
                    "kind": "lore",
                    "chunk_id": c.chunk_id,
                },
            )
            for i, c in enumerate(chunks)
        ]
        self.client.upsert(collection_name=self.settings.lore_collection, points=points)
        return len(points)

    def upsert_memory(
        self,
        *,
        text: str,
        vector: list[float],
        role: str,
        player: str | None,
        event_type: str | None,
    ) -> None:
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.settings.memory_collection,
            points=[
                qm.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": text,
                        "kind": "memory",
                        "role": role,
                        "player": player or "",
                        "event_type": event_type or "",
                        "ts": time.time(),
                    },
                )
            ],
        )

    def search(
        self,
        collection: str,
        vector: list[float],
        *,
        top_k: int,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "collection_name": collection,
            "query_vector": vector,
            "limit": top_k,
            "with_payload": True,
        }
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold
        hits = self.client.search(**kwargs)
        out: list[dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            out.append(
                {
                    "id": hit.id,
                    "score": float(hit.score),
                    "text": str(payload.get("text", "")),
                    "source": str(payload.get("source", "")),
                    "title": str(payload.get("title", "")),
                    "kind": str(payload.get("kind", "")),
                    "role": str(payload.get("role", "")),
                    "player": str(payload.get("player", "")),
                    "event_type": str(payload.get("event_type", "")),
                }
            )
        return out

    def clear_lore(self) -> None:
        name = self.settings.lore_collection
        if self.client.collection_exists(name):
            self.client.delete_collection(name)
        self._ensure_collection(name, self.settings.embedding_dims)

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        # Qdrant accepts UUID or unsigned int; use UUID5 from chunk_id
        return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
