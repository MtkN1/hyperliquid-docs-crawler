from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import typer
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from ._parse import DocEntry, parse_llms_markdown

DEFAULT_LLMS_URL = "https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt"

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _default_progress() -> Progress:
    return Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        transient=True,
        expand=True,
    )


def fetch_text(url: str, client: httpx.Client | None = None) -> str:
    """Fetch text content from URL with optional shared client."""

    if client is None:
        with httpx.Client() as session:
            response = session.get(url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return response.text

    response = client.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def download_docs(
    llms_url: str,
    output_dir: Path,
    client: httpx.Client | None = None,
    progress: Progress | None = None,
) -> list[Path]:
    """Download all documents listed in llms.txt into the output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)

    if client is None:
        with httpx.Client() as session:
            return _download_with_client(
                llms_url=llms_url,
                output_dir=output_dir,
                client=session,
                progress=progress,
            )

    return _download_with_client(
        llms_url=llms_url, output_dir=output_dir, client=client, progress=progress
    )


def _download_with_client(
    llms_url: str, output_dir: Path, client: httpx.Client, progress: Progress | None
) -> list[Path]:
    llms_text = fetch_text(llms_url, client=client)
    parsed_url = urlparse(llms_url)
    llms_path = output_dir / Path(parsed_url.path.lstrip("/"))
    llms_path.parent.mkdir(parents=True, exist_ok=True)
    llms_path.write_text(llms_text, encoding="utf-8")

    entries = parse_llms_markdown(llms_text)
    written: list[Path] = []
    seen: set[str] = set()

    unique_entries: list[DocEntry] = []
    for entry in entries:
        if entry.href in seen:
            continue
        seen.add(entry.href)
        unique_entries.append(entry)

    progress_obj = progress or _default_progress()
    with progress_obj if progress is None else nullcontext():
        task_id = progress_obj.add_task("Downloading docs", total=len(unique_entries))

        for entry in unique_entries:
            target_url = urljoin(llms_url, entry.href)
            doc = fetch_text(target_url, client=client)

            destination = output_dir / entry.href.lstrip("/")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(doc, encoding="utf-8")

            written.append(destination)
            progress_obj.update(task_id, advance=1)

    return written


def run_download(
    llms_url: str = DEFAULT_LLMS_URL, output_dir: Path = Path("dist")
) -> list[Path]:
    return download_docs(llms_url=llms_url, output_dir=output_dir)


@app.command()
def main(
    llms_url: str = typer.Option(
        DEFAULT_LLMS_URL,
        "--llms-url",
        help="URL pointing to llms.txt index",
        show_default=True,
    ),
    output_dir: Path = typer.Option(
        Path("dist"),
        "--output-dir",
        "-o",
        help="Directory to store downloaded docs",
        show_default=True,
    ),
) -> None:
    written = run_download(llms_url=llms_url, output_dir=output_dir)
    typer.echo(f"Downloaded {len(written)} files to {output_dir}")
