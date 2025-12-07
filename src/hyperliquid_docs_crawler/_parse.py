from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass(frozen=True, slots=True)
class DocEntry:
    """Represents a single document link discovered in the index."""

    title: str
    href: str
    section: tuple[str, ...]
    note: str | None = None


def parse_llms_markdown(markdown: str) -> list[DocEntry]:
    """Parse the llms.txt Markdown index into structured document links.

    The parser walks headings to build a section breadcrumb and collects
    links that appear inside list items. Any trailing text in the bullet is
    treated as a note (with leading punctuation removed).
    """

    parser = MarkdownIt()
    tokens = parser.parse(markdown)

    section_stack: list[str] = []
    entries: list[DocEntry] = []
    in_list_item = False

    for idx, token in enumerate(tokens):
        if token.type == "heading_open":
            _update_section_stack(tokens, idx, section_stack)
        elif token.type == "list_item_open":
            in_list_item = True
        elif token.type == "list_item_close":
            in_list_item = False
        elif token.type == "inline" and in_list_item:
            entry = _entry_from_inline(token, section_stack)
            if entry:
                entries.append(entry)

    return entries


def parse_llms_file(path: str | Path) -> list[DocEntry]:
    """Read and parse ``llms.txt`` located at ``path``."""

    content = Path(path).read_text(encoding="utf-8")
    return parse_llms_markdown(content)


def _update_section_stack(
    tokens: list[Token], idx: int, section_stack: list[str]
) -> None:
    heading_open = tokens[idx]
    tag = heading_open.tag
    if len(tag) < 2 or not tag[1].isdigit():
        return

    level = int(tag[1])

    title = _heading_title(tokens, idx)
    if not title:
        return

    # Keep ancestors up to the current level, then replace the current level.
    del section_stack[level - 1 :]
    section_stack.append(title)


def _heading_title(tokens: list[Token], idx: int) -> str | None:
    if idx + 1 >= len(tokens):
        return None
    inline = tokens[idx + 1]
    if inline.type != "inline":
        return None
    title = inline.content.strip()
    return title or None


def _entry_from_inline(inline: Token, section_stack: Iterable[str]) -> DocEntry | None:
    href: str | None = None
    title_parts: list[str] = []
    note_parts: list[str] = []
    in_link = False

    for child in inline.children or []:
        if child.type == "link_open":
            href = (child.attrs or {}).get("href")
            in_link = True
        elif child.type == "link_close":
            in_link = False
        elif child.type == "text" and in_link:
            title_parts.append(child.content)
        elif child.type == "text":
            note_parts.append(child.content)

    if not href or not title_parts:
        return None

    note = "".join(note_parts).strip()
    note = note.lstrip(":").strip()
    note = note or None

    title = "".join(title_parts).strip()
    if not title:
        return None

    return DocEntry(
        title=title, href=href.strip(), section=tuple(section_stack), note=note
    )


__all__ = ["DocEntry", "parse_llms_file", "parse_llms_markdown"]
