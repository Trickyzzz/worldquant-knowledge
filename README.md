# worldquant-knowledge

Build a local, NotebookLM-ready knowledge base from WorldQuant learning sources.

[中文说明](README.zh-CN.md)

`worldquant-knowledge` exports public WorldQuant pages and read-only WorldQuant BRAIN reference data into clean, partitioned Markdown files. The goal is simple: keep operators, datasets, fields, public articles, and your own notes searchable in one NotebookLM notebook without mixing in demo data or empty placeholders.

## What It Exports

- WorldQuant public pages through Firecrawl
- WorldQuant BRAIN operators
- WorldQuant BRAIN datasets
- WorldQuant BRAIN fields
- Derived alpha-pattern views from exported source material
- Optional local notes from `my_notes_input/`

The exporter does not crawl logged-in courses, forums, community posts, other users' alphas, comments, or ranking details.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
New-Item -ItemType Directory -Force secrets
```

Add your local credentials:

```text
secrets/firecrawl_apikey.txt
secrets/worldquant_brain_cookie.txt
```

Then run:

```powershell
.\.venv\Scripts\python sync.py --all
```

## Output

Generated NotebookLM sources are written to:

```text
notebooklm_sources/
  00_index.md
  operators/
  datasets_and_fields/
  alpha_patterns/
  public_articles/
  my_notes/
```

Only sections backed by real input are generated. For example, `public_articles/` is omitted until public pages are actually crawled, and `my_notes/` is omitted until local notes exist.

Raw export cache and crawl logs are written separately:

```text
raw/
crawl_manifest.csv
```

## Source Rules

The final Markdown output is not populated with demo, fixture, sample, or placeholder content.

- `operators/` and `datasets_and_fields/` are rendered from exported BRAIN data.
- `alpha_patterns/` is derived from exported operators, fields, public articles, and local notes.
- Index files are generated to help NotebookLM understand the source structure.
- Empty source partitions are skipped.

## Commands

```powershell
.\.venv\Scripts\python sync.py --all
.\.venv\Scripts\python sync.py --public
.\.venv\Scripts\python sync.py --brain
.\.venv\Scripts\python sync.py --notes
.\.venv\Scripts\python sync.py --build
.\.venv\Scripts\python sync.py --all --incremental
```

Use `--build` when you already have cached data in `raw/` and only want to regenerate Markdown.

Use `--incremental` with `--all`, `--public`, or `--brain` to reuse existing raw exports when present. Missing cache files are fetched normally.

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit as needed.

Important defaults:

```yaml
public_crawl:
  max_pages: 1000
  max_depth: 5

brain:
  delay_seconds: 2
  max_requests_per_run: 500
  max_rate_limit_retries: 12
  rate_limit_backoff_seconds: 60
  max_rate_limit_sleep_seconds: 900
```

`config.yaml`, `secrets/`, `raw/`, and `notebooklm_sources/` are ignored by git.

## Rate Limits

WorldQuant BRAIN does not publish a stable public limit for the internal read-only endpoints used by the web app. When the exporter receives `429`, it waits for `Retry-After` if provided; otherwise it uses exponential backoff. The default retry policy is intentionally conservative.

## Import Into NotebookLM

Create one NotebookLM notebook and upload the Markdown files from `notebooklm_sources/`. Keeping the files split by topic usually gives better retrieval and citations than uploading one huge Markdown file.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Notes

This project is designed for personal learning workflows. Use it only with material you are allowed to access, and keep request limits conservative.
