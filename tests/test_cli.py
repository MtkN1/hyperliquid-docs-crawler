from pathlib import Path
from typing import Any

import httpx
from httpx import MockTransport, Request, Response
from typer.testing import CliRunner

from hyperliquid_docs_crawler import app, download_docs, fetch_text

runner = CliRunner()
LLMS_URL = "https://example.com/hyperliquid-docs/llms.txt"


class DummyProgress:
    def __init__(self) -> None:
        self.updates: list[int] = []

    def add_task(self, *_: object, total: int = 0, **__: object) -> int:
        self.total = total
        return 1

    def update(self, task_id: int, advance: int = 0, **__: object) -> None:
        self.updates.append(advance)


def test_download_docs_writes_files(tmp_path: Path) -> None:
    llms_body = """
# Docs
- [About](/hyperliquid-docs/about.md)
- [About](/hyperliquid-docs/about.md)
- [Guide](/hyperliquid-docs/guide.md)
"""

    def handler(request: Request) -> Response:
        if request.url.path == "/hyperliquid-docs/llms.txt":
            return Response(200, text=llms_body)
        if request.url.path == "/hyperliquid-docs/about.md":
            return Response(200, text="# About")
        if request.url.path == "/hyperliquid-docs/guide.md":
            return Response(200, text="# Guide")
        return Response(404)

    client = httpx.Client(
        transport=MockTransport(handler), base_url="https://example.com"
    )

    progress = DummyProgress()

    written = download_docs(
        LLMS_URL,
        tmp_path / "out",
        client=client,
        progress=progress,
    )

    assert len(written) == 2
    about = tmp_path / "out" / "hyperliquid-docs" / "about.md"
    guide = tmp_path / "out" / "hyperliquid-docs" / "guide.md"

    assert about.read_text(encoding="utf-8") == "# About"
    assert guide.read_text(encoding="utf-8") == "# Guide"
    assert written == [about, guide]
    assert sum(progress.updates) == 2


def test_download_docs_stores_index(tmp_path: Path) -> None:
    llms_body = """
# Docs
- [About](/hyperliquid-docs/about.md)
- [Guide](/hyperliquid-docs/guide.md)
"""

    def handler(request: Request) -> Response:
        if request.url.path == "/hyperliquid-docs/llms.txt":
            return Response(200, text=llms_body)
        if request.url.path == "/hyperliquid-docs/about.md":
            return Response(200, text="# About")
        if request.url.path == "/hyperliquid-docs/guide.md":
            return Response(200, text="# Guide")
        return Response(404)

    client = httpx.Client(
        transport=MockTransport(handler), base_url="https://example.com"
    )

    download_docs(LLMS_URL, tmp_path / "out", client=client)

    llms_file = tmp_path / "out" / "hyperliquid-docs" / "llms.txt"
    assert llms_file.exists()
    assert llms_file.read_text(encoding="utf-8") == llms_body


def test_fetch_text_closes_created_client(monkeypatch: Any) -> None:
    class DummyResponse:
        def __init__(self) -> None:
            self.text = "body"
            self.encoding = None

        def raise_for_status(self) -> None:
            return None

    class DummyClient:
        def __init__(self) -> None:
            self.closed = False

        def get(self, *_: Any, **__: Any) -> DummyResponse:
            return DummyResponse()

        def close(self) -> None:
            self.closed = True

        def __enter__(self) -> "DummyClient":
            return self

        def __exit__(self, *_: object) -> None:
            self.close()

    dummy_client = DummyClient()
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: dummy_client)

    result = fetch_text("https://example.com/foo")

    assert result == "body"
    assert dummy_client.closed is True


def test_cli_invokes_run_download(monkeypatch: Any, tmp_path: Path) -> None:
    called = {}

    def fake_run_download(llms_url: str, output_dir: Path) -> list[Path]:
        called["args"] = (llms_url, output_dir)
        dest = output_dir / "file.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("content", encoding="utf-8")
        return [dest]

    monkeypatch.setattr("hyperliquid_docs_crawler._cli.run_download", fake_run_download)

    result = runner.invoke(
        app,
        ["--llms-url", LLMS_URL, "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "Downloaded 1 files" in result.stdout
    assert called["args"][0] == LLMS_URL
    assert called["args"][1] == tmp_path
