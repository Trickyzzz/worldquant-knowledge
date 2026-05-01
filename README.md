# worldquant-knowledge

Personal WorldQuant learning-source exporter for NotebookLM.

The tool collects low-risk learning material from public WorldQuant pages and read-only WorldQuant BRAIN structured data, then writes partitioned Markdown files under `notebooklm_sources/`.

## What You Provide

- Firecrawl API key file: `secrets/firecrawl_apikey.txt`
- WorldQuant BRAIN logged-in cookie/session file: `secrets/worldquant_brain_cookie.txt`
- Optional notes: Markdown or text files under `my_notes_input/`

You do not provide a WorldQuant password, NotebookLM account, Google account, or a complete URL list.

## Boundaries

This is not a full-platform crawler. It does not export logged-in courses, forum/community posts, other users' alphas, comments, or ranking details. It uses conservative read-only BRAIN endpoints with rate limits and keeps secrets out of source control.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
New-Item -ItemType Directory -Force secrets
```

Put your Firecrawl key in `secrets/firecrawl_apikey.txt` and your logged-in WorldQuant BRAIN cookie/session in `secrets/worldquant_brain_cookie.txt`. The `secrets/` directory is ignored by git.

## Rate Limits

WorldQuant BRAIN does not publish a stable user-facing limit for these internal read-only endpoints. The exporter handles this automatically: when BRAIN returns `429`, it waits for `Retry-After` when provided, otherwise uses exponential backoff. The defaults retry up to 12 times and cap each wait at 15 minutes.

## Run

```powershell
.\.venv\Scripts\python sync.py --all
```

Generated output:

```text
notebooklm_sources/
  00_index.md
  operators/
  datasets_and_fields/
  alpha_patterns/
  public_articles/
  my_notes/
```

Also generated:

```text
raw/
crawl_manifest.csv
```

## Import Into NotebookLM

Create one NotebookLM notebook and upload the Markdown files in `notebooklm_sources/`.

## Maintenance

- Add personal notes to `my_notes_input/`.
- Adjust public seeds or limits in `config.yaml`.
- If BRAIN endpoints change, update `worldquant_knowledge/brain_client.py`.
