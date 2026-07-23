"""Unit tests for chunking / session (без Qdrant/Azure)."""

from __future__ import annotations

from pathlib import Path

from app.rag.chunking import load_knowledge_chunks, split_markdown_file
from app.rag.session import SessionMemory


def test_split_markdown_by_headings(tmp_path: Path) -> None:
    path = tmp_path / "t.md"
    path.write_text(
        "# Title A\n\nHello world paragraph.\n\n## Title B\n\nSecond block text here.\n",
        encoding="utf-8",
    )
    chunks = split_markdown_file(path, chunk_size=500, chunk_overlap=50)
    assert len(chunks) >= 2
    assert any("Title A" in c.title or "Title A" in c.text for c in chunks)
    assert all(c.kind == "lore" for c in chunks)


def test_load_bundled_knowledge() -> None:
    root = Path(__file__).resolve().parents[1] / "knowledge"
    chunks = load_knowledge_chunks(root, chunk_size=900, chunk_overlap=150)
    assert len(chunks) >= 4
    sources = {c.source for c in chunks}
    assert "01_philosophy.md" in sources


def test_session_recent_and_prompt() -> None:
    mem = SessionMemory(store=None)
    mem.add("event", "Dev → death", player="Dev", event_type="death", persist_vector=False)
    mem.add("observer", "Тильт на линии.", persist_vector=False)
    mem.add("observer", "Снова угарный фасад.", persist_vector=False)
    assert len(mem.recent_observer_lines()) == 2
    block = mem.as_prompt_block()
    assert "Бог А" in block
    assert "не повторяй" in block.lower() or "Недавний" in block


def test_session_persistence(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    mem = SessionMemory(store=None, persist_path=path)
    mem.add("event", "Kostyan → join", player="Kostyan", event_type="join", persist_vector=False)
    mem.add("observer", "здаров додик", persist_vector=False)
    assert path.exists()

    # Новый инстанс с того же файла — история восстановлена (пережила «рестарт»)
    mem2 = SessionMemory(store=None, persist_path=path)
    turns = mem2.recent()
    assert len(turns) == 2
    assert any(t.role == "observer" and "здаров" in t.text for t in turns)
