from __future__ import annotations

from pathlib import Path

from .brain_client import InternalBrainClient
from .builders import build_sources, write_json, write_manifest
from .config import Config
from .firecrawl_client import FirecrawlPublicClient
from .notes import load_notes


def run_public(config: Config) -> list[dict[str, object]]:
    if not config.public_crawl.enabled:
        return []
    client = FirecrawlPublicClient(config.firecrawl_api_key)
    per_seed_limit = max(1, config.public_crawl.max_pages // max(1, len(config.public_crawl.seed_urls)))
    seen: set[str] = set()
    articles: list[dict[str, object]] = []
    manifest: list[dict[str, object]] = []
    for seed_url in config.public_crawl.seed_urls:
        try:
            for article in client.crawl_seed(
                seed_url,
                per_seed_limit,
                max_depth=config.public_crawl.max_depth,
                use_sitemap=config.public_crawl.use_sitemap,
                delay_seconds=config.public_crawl.delay_seconds,
                exclude_patterns=config.public_crawl.exclude_patterns,
            ):
                if article.url in seen or _excluded(article.url, config.public_crawl.exclude_patterns):
                    continue
                seen.add(article.url)
                item = {
                    "title": article.title,
                    "url": article.url,
                    "markdown": article.markdown,
                    "category": article.category,
                }
                articles.append(item)
                manifest.append({"url": article.url, "title": article.title, "category": article.category, "status": "ok"})
        except Exception as exc:
            manifest.append({"url": seed_url, "title": "", "category": "seed", "status": "failed", "error": str(exc)})
    write_json(config.output.raw_dir / "public_articles.json", articles)
    write_manifest(Path("crawl_manifest.csv"), manifest)
    return articles


def run_brain(config: Config) -> tuple[list[dict], list[dict], list[dict]]:
    if not config.brain.enabled:
        return [], [], []
    client = InternalBrainClient(
        base_url=config.brain.base_url,
        cookie=config.brain.cookie,
        delay_seconds=config.brain.delay_seconds,
        max_requests_per_run=config.brain.max_requests_per_run,
        region=config.brain.region,
        delay=config.brain.delay,
        universe=config.brain.universe,
        max_rate_limit_retries=config.brain.max_rate_limit_retries,
        rate_limit_backoff_seconds=config.brain.rate_limit_backoff_seconds,
        max_rate_limit_sleep_seconds=config.brain.max_rate_limit_sleep_seconds,
    )
    operators = client.get_operators() if config.brain.export.get("operators") else []
    datasets = client.get_datasets() if config.brain.export.get("datasets") else []
    fields = client.get_fields() if config.brain.export.get("fields") else []
    write_json(config.output.raw_dir / "brain" / "operators.json", operators)
    write_json(config.output.raw_dir / "brain" / "datasets.json", datasets)
    write_json(config.output.raw_dir / "brain" / "fields.json", fields)
    return operators, datasets, fields


def run_notes(config: Config) -> list[dict[str, str]]:
    if not config.notes.enabled:
        return []
    return load_notes(config.notes.input_dir)


def build_all(
    config: Config,
    public_articles: list[dict],
    operators: list[dict],
    datasets: list[dict],
    fields: list[dict],
    notes: list[dict[str, str]],
) -> None:
    build_sources(
        output_dir=config.output.dir,
        public_articles=public_articles,
        operators=operators,
        datasets=datasets,
        fields=fields,
        notes=notes,
        max_words_per_file=config.output.max_words_per_file,
    )


def _excluded(url: str, patterns: list[str]) -> bool:
    lowered = url.lower()
    return any(pattern.lower() in lowered for pattern in patterns)
