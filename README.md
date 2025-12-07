# hyperliquid-docs-crawler

Retrieve Hyperliquid DEX docs as Markdown files.

## Requirements

- Python 3.14 or newer (project is built with `uv`).

## Installation

1. Install the package using `uv` so you can run the CLI directly:
	```bash
	uv sync
	```

## Usage

1. Run the crawler with the Typer CLI. The default command fetches the GitBook index hosted at `https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt` and writes everything under `dist/`:
	```bash
	uv run -m hyperliquid_docs_crawler
	```
2. Override the defaults with the available options:
	- `--llms-url <url>`: alternative index (default `https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt`).
	- `-o/--output-dir <dir>`: directory where downloaded files land (default `dist`).
3. Each run preserves the fetched index as `llms.txt` inside the output directory under the path derived from the index URL (e.g., `dist/hyperliquid-docs/llms.txt`). Documents are saved according to their href paths (e.g., `dist/hyperliquid-docs/about.md`), and duplicate links are skipped so the same file is not downloaded twice.
4. A Rich progress bar animates while downloading, and the CLI prints `Downloaded <N> files to <output-dir>` upon completion.

## Output structure

- Downloaded Markdown files keep the same directory layout as the GitBook hrefs that appear in the index.
- The crawler normalizes each href and removes duplicates based on the target path before downloading.
- If the index list contains notes (text after the link in the same bullet), the parser retains them to surface additional metadata when necessary.

## Testing

Use `uv` to run the test suite so it executes inside the same environment:
```bash
uv run pytest
```

## Continuous Integration

GitHub Actions CI is included and runs pytest on push and pull requests. The workflow is defined in
`.github/workflows/ci.yml` and tests on Python 3.14+.
