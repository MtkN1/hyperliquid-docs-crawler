from pathlib import Path

from hyperliquid_docs_crawler import DocEntry, parse_llms_file, parse_llms_markdown

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "llms.txt"


def test_parse_llms_markdown_sections_and_notes() -> None:
    markdown = """
# Root
## Section A
- [Foo](/foo.md): Note here
### Subsection
- [Bar](/bar.md)
"""

    entries = parse_llms_markdown(markdown)

    assert entries == [
        DocEntry(
            title="Foo", href="/foo.md", section=("Root", "Section A"), note="Note here"
        ),
        DocEntry(
            title="Bar",
            href="/bar.md",
            section=("Root", "Section A", "Subsection"),
            note=None,
        ),
    ]


def test_parse_llms_file_reads_fixture() -> None:
    entries = parse_llms_file(FIXTURE_PATH)

    assert len(entries) > 70

    first = entries[0]
    assert first.title == "About Hyperliquid"
    assert first.href == "/hyperliquid-docs/about-hyperliquid.md"
    assert first.section == ("Hyperliquid Docs", "Hyperliquid Docs")
    assert first.note is None

    multisig = next(
        entry for entry in entries if entry.href.endswith("/hypercore/multi-sig.md")
    )
    assert multisig.note == "Advanced Feature"


def test_parse_llms_file_keeps_description_text() -> None:
    entries = parse_llms_file(FIXTURE_PATH)

    described = next(
        entry for entry in entries if entry.title == "Connected via wallet"
    )

    assert described.note is not None
    assert described.note.startswith("Description:")


def test_parse_llms_markdown_without_headings_uses_empty_section() -> None:
    markdown = """
- [Foo](/foo.md)
"""

    entries = parse_llms_markdown(markdown)

    assert entries == [DocEntry(title="Foo", href="/foo.md", section=(), note=None)]


def test_parse_llms_markdown_skips_items_without_links() -> None:
    markdown = """
## Section
- No links here
"""

    entries = parse_llms_markdown(markdown)

    assert entries == []
