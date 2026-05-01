from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class FirecrawlExportError(RuntimeError):
    """Raised when public content crawling fails."""


@dataclass(frozen=True)
class PublicArticle:
    title: str
    url: str
    markdown: str
    category: str


class FirecrawlPublicClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def crawl_seed(
        self,
        url: str,
        limit: int,
        max_depth: int = 5,
        use_sitemap: bool = True,
        delay_seconds: float = 1.0,
        exclude_patterns: list[str] | None = None,
    ) -> list[PublicArticle]:
        try:
            from firecrawl import Firecrawl
            from firecrawl.v2.types import ScrapeOptions
        except Exception as exc:  # pragma: no cover - depends on optional installed package
            raise FirecrawlExportError("Install the firecrawl package from requirements.txt.") from exc

        client = Firecrawl(api_key=self.api_key)
        try:
            docs = client.crawl(
                url=url,
                limit=limit,
                max_discovery_depth=max_depth,
                sitemap="include" if use_sitemap else "skip",
                exclude_paths=exclude_patterns or None,
                delay=int(delay_seconds) if delay_seconds >= 1 else None,
                scrape_options=ScrapeOptions(formats=["markdown"], only_main_content=True),
            )
        except Exception as exc:  # pragma: no cover - external API
            raise FirecrawlExportError(f"Firecrawl failed for {url}: {exc}") from exc
        return self._articles_from_docs(docs)

    def _articles_from_docs(self, docs: Any) -> list[PublicArticle]:
        data = getattr(docs, "data", docs)
        if isinstance(data, dict):
            data = data.get("data") or data.get("results") or [data]
        articles: list[PublicArticle] = []
        for item in data or []:
            markdown = _read_attr_or_key(item, "markdown") or ""
            metadata = _read_attr_or_key(item, "metadata") or {}
            url = _read_attr_or_key(metadata, "sourceURL") or _read_attr_or_key(metadata, "url") or ""
            title = _read_attr_or_key(metadata, "title") or url or "Untitled"
            if markdown and url:
                articles.append(
                    PublicArticle(
                        title=str(title),
                        url=str(url),
                        markdown=str(markdown),
                        category=_category_for_url(str(url)),
                    )
                )
        return articles


def _read_attr_or_key(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _category_for_url(url: str) -> str:
    lowered = url.lower()
    if "learn2quant" in lowered:
        return "learn2quant"
    if "/brain/iqc" in lowered:
        return "iqc"
    if "/brain" in lowered:
        return "worldquant_brain"
    if "/ideas" in lowered:
        return "research_and_ai"
    return "worldquant"
