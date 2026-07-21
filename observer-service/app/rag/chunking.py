"""Чанкинг markdown-знаний для индексации."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    source: str
    title: str
    kind: str  # lore | memory


_HEADING = re.compile(r"(?m)^(#{1,3})\s+(.+)$")


def _stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:32]


def split_markdown_file(
    path: Path,
    *,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[TextChunk]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    source = path.name
    sections = _split_by_headings(raw)
    chunks: list[TextChunk] = []

    for title, body in sections:
        body = body.strip()
        if not body:
            continue
        pieces = _window(body, chunk_size=chunk_size, overlap=chunk_overlap)
        for i, piece in enumerate(pieces):
            text = f"{title}\n\n{piece}".strip() if title else piece
            chunks.append(
                TextChunk(
                    chunk_id=_stable_id(source, title, str(i), piece),
                    text=text,
                    source=source,
                    title=title or source,
                    kind="lore",
                )
            )
    return chunks


def _split_by_headings(text: str) -> list[tuple[str, str]]:
    matches = list(_HEADING.finditer(text))
    if not matches:
        return [("", text)]

    sections: list[tuple[str, str]] = []
    # preamble before first heading
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            sections.append(("", pre))

    for idx, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append((title, body))
    return sections


def _window(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    overlap = max(0, min(overlap, chunk_size // 2))
    step = max(1, chunk_size - overlap)
    out: list[str] = []
    i = 0
    while i < len(text):
        out.append(text[i : i + chunk_size].strip())
        if i + chunk_size >= len(text):
            break
        i += step
    return [c for c in out if c]


def load_knowledge_chunks(
    knowledge_dir: Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    if not knowledge_dir.is_dir():
        return []
    files = sorted(knowledge_dir.glob("*.md"))
    chunks: list[TextChunk] = []
    for path in files:
        chunks.extend(
            split_markdown_file(path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        )
    return chunks
