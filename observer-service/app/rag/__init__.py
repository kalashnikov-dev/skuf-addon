"""RAG: embeddings + Qdrant + session memory для наблюдателя."""

from app.rag.pipeline import RagPipeline, get_pipeline, rag_status

__all__ = ["RagPipeline", "get_pipeline", "rag_status"]
