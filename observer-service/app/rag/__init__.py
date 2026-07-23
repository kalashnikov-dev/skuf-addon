"""RAG: embeddings + Qdrant + session memory для наблюдателя."""

from app.rag.extract import auto_extraction_enabled, extract_facts
from app.rag.facts import Fact, FactStore
from app.rag.pipeline import RagPipeline, get_pipeline, rag_status

__all__ = [
    "RagPipeline",
    "get_pipeline",
    "rag_status",
    "FactStore",
    "Fact",
    "extract_facts",
    "auto_extraction_enabled",
]
