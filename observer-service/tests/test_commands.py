"""Юниты parse_memory_command: детерминированный парсинг «запомни X»."""

from __future__ import annotations

from app.main import parse_memory_command


def test_plain_remember() -> None:
    assert parse_memory_command("запомни евген") == "евген"


def test_remember_with_quotes() -> None:
    assert parse_memory_command('запомни "евген"') == '"евген"'


def test_remember_colon_and_chto() -> None:
    assert parse_memory_command("запомни: кто это") == "кто это"
    assert parse_memory_command("запомни, что тешка спит по 18 часов") == "тешка спит по 18 часов"


def test_remember_case_insensitive() -> None:
    assert parse_memory_command("ЗАПОМНИ арсен лох") == "арсен лох"


def test_empty_command() -> None:
    # Команда есть, но содержимого нет → "" (пустая строка, не None)
    assert parse_memory_command("запомни") == ""
    assert parse_memory_command("запомни   ") == ""


def test_not_a_command() -> None:
    assert parse_memory_command("что ты запомнил") is None
    assert parse_memory_command("привет как дела") is None
    assert parse_memory_command("") is None
