"""Юниты FactStore: запись, дедуп, персистентность, prompt-блок (без Qdrant/Azure)."""

from __future__ import annotations

from pathlib import Path

from app.rag.facts import FactStore, _normalize


def test_remember_and_persist(tmp_path: Path) -> None:
    path = tmp_path / "facts.json"
    store = FactStore(path)
    assert store.remember("евген это кент из деревни", player="Kostyan") is True
    assert store.count() == 1
    assert path.exists()

    # Новый инстанс с того же файла — факт на месте (пережил «рестарт»)
    store2 = FactStore(path)
    assert store2.count() == 1
    assert "евген" in store2.as_prompt_block().lower()


def test_dedup(tmp_path: Path) -> None:
    store = FactStore(tmp_path / "facts.json")
    assert store.remember("Тешка удалил доту") is True
    # Дубль с другим регистром/пунктуацией/пробелами — не добавляется
    assert store.remember("  тешка УДАЛИЛ доту.  ") is False
    assert store.count() == 1


def test_empty_not_stored(tmp_path: Path) -> None:
    store = FactStore(tmp_path / "facts.json")
    assert store.remember("") is False
    assert store.remember("   ") is False
    assert store.count() == 0
    assert store.as_prompt_block() == ""


def test_normalize() -> None:
    assert _normalize("  Привет, МИР!! ") == "привет, мир"
    assert _normalize('"евген"') == "евген"


def test_prompt_block_lists_facts(tmp_path: Path) -> None:
    store = FactStore(tmp_path / "facts.json")
    store.remember("арсену мамка гладит рубашки", player="Artur")
    block = store.as_prompt_block()
    assert "запомненные факты" in block.lower()
    assert "арсен" in block.lower()
    assert "(от Artur)" in block
