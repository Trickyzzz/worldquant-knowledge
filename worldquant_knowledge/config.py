from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_SEED_URLS = [
    "https://www.worldquant.com/",
    "https://www.worldquant.com/brain/",
    "https://www.worldquant.com/learn2quant/",
    "https://www.worldquant.com/ideas/",
    "https://www.worldquant.com/brain/iqc/",
    "https://www.worldquant.com/brain/iqc-guidelines/",
]


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class PublicCrawlConfig:
    enabled: bool = True
    seed_urls: list[str] = field(default_factory=lambda: list(DEFAULT_SEED_URLS))
    allowed_domains: list[str] = field(default_factory=lambda: ["worldquant.com"])
    use_sitemap: bool = True
    max_pages: int = 1000
    max_depth: int = 5
    include_pdf: bool = True
    delay_seconds: float = 1.0
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["/careers/", "/privacy", "/terms", "/cookie", "/contact"]
    )


@dataclass(frozen=True)
class BrainConfig:
    enabled: bool = True
    client_type: str = "internal"
    base_url: str = "https://api.worldquantbrain.com"
    cookie_file: Path | None = None
    cookie: str = ""
    delay_seconds: float = 2.0
    max_requests_per_run: int = 500
    max_rate_limit_retries: int = 12
    rate_limit_backoff_seconds: float = 60.0
    max_rate_limit_sleep_seconds: float = 900.0
    region: str = "USA"
    delay: int = 1
    universe: str = "TOP3000"
    export: dict[str, bool] = field(
        default_factory=lambda: {
            "operators": True,
            "datasets": True,
            "fields": True,
            "my_alphas": False,
            "simulations": False,
            "courses": False,
            "forum_posts": False,
        }
    )


@dataclass(frozen=True)
class OutputConfig:
    dir: Path = Path("notebooklm_sources")
    raw_dir: Path = Path("raw")
    processed_dir: Path = Path("processed")
    max_words_per_file: int = 30000


@dataclass(frozen=True)
class NotesConfig:
    enabled: bool = True
    input_dir: Path = Path("my_notes_input")


@dataclass(frozen=True)
class Config:
    firecrawl_api_key: str
    public_crawl: PublicCrawlConfig
    brain: BrainConfig
    output: OutputConfig
    notes: NotesConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a YAML mapping.")
    return data


def _read_secret_file(path: Path, label: str) -> str:
    if not path.exists():
        raise ConfigError(f"Missing {label} file: {path}")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ConfigError(f"{label} file is empty: {path}")
    return value


def _resolve_path(value: str | Path | None, base_dir: Path) -> Path | None:
    if value is None or value == "":
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path


def load_config(path: str | Path = "config.yaml") -> Config:
    config_path = Path(path)
    data = _read_yaml(config_path)
    base_dir = config_path.parent.resolve()

    firecrawl_key = (data.get("firecrawl_api_key") or os.getenv("FIRECRAWL_API_KEY") or "").strip()
    firecrawl_key_file = _resolve_path(data.get("firecrawl_api_key_file"), base_dir)
    if not firecrawl_key and firecrawl_key_file:
        firecrawl_key = _read_secret_file(firecrawl_key_file, "Firecrawl API key")
    if not firecrawl_key:
        raise ConfigError("Missing Firecrawl API key. Set FIRECRAWL_API_KEY or firecrawl_api_key_file.")

    public_data = data.get("public_crawl") or {}
    public_crawl = PublicCrawlConfig(
        enabled=bool(public_data.get("enabled", True)),
        seed_urls=list(public_data.get("seed_urls") or DEFAULT_SEED_URLS),
        allowed_domains=list(public_data.get("allowed_domains") or ["worldquant.com"]),
        use_sitemap=bool(public_data.get("use_sitemap", True)),
        max_pages=int(public_data.get("max_pages", 1000)),
        max_depth=int(public_data.get("max_depth", 5)),
        include_pdf=bool(public_data.get("include_pdf", True)),
        delay_seconds=float(public_data.get("delay_seconds", 1.0)),
        exclude_patterns=list(
            public_data.get("exclude_patterns")
            or ["/careers/", "/privacy", "/terms", "/cookie", "/contact"]
        ),
    )
    if public_crawl.enabled and not public_crawl.seed_urls:
        raise ConfigError("No public seed URLs configured.")

    brain_data = data.get("brain") or {}
    brain_enabled = bool(brain_data.get("enabled", True))
    cookie_file = _resolve_path(brain_data.get("cookie_file"), base_dir)
    cookie = ""
    if brain_enabled:
        if cookie_file is None:
            raise ConfigError("Missing WorldQuant BRAIN cookie_file while brain.enabled=true.")
        cookie = _read_secret_file(cookie_file, "WorldQuant BRAIN cookie")

    output_data = data.get("output") or {}
    output = OutputConfig(
        dir=Path(output_data.get("dir", "notebooklm_sources")),
        raw_dir=Path(output_data.get("raw_dir", "raw")),
        processed_dir=Path(output_data.get("processed_dir", "processed")),
        max_words_per_file=int(output_data.get("max_words_per_file", 30000)),
    )

    notes_data = data.get("my_notes") or data.get("notes") or {}
    notes = NotesConfig(
        enabled=bool(notes_data.get("enabled", True)),
        input_dir=Path(notes_data.get("input_dir", "my_notes_input")),
    )

    brain = BrainConfig(
        enabled=brain_enabled,
        client_type=str(brain_data.get("client_type", "internal")),
        base_url=str(brain_data.get("base_url", "https://api.worldquantbrain.com")).rstrip("/"),
        cookie_file=cookie_file,
        cookie=cookie,
        delay_seconds=float(brain_data.get("delay_seconds", 2.0)),
        max_requests_per_run=int(brain_data.get("max_requests_per_run", 500)),
        max_rate_limit_retries=int(brain_data.get("max_rate_limit_retries", 12)),
        rate_limit_backoff_seconds=float(brain_data.get("rate_limit_backoff_seconds", 60.0)),
        max_rate_limit_sleep_seconds=float(brain_data.get("max_rate_limit_sleep_seconds", 900.0)),
        region=str(brain_data.get("region", "USA")),
        delay=int(brain_data.get("delay", 1)),
        universe=str(brain_data.get("universe", "TOP3000")),
        export=dict(
            {
                "operators": True,
                "datasets": True,
                "fields": True,
                "my_alphas": False,
                "simulations": False,
                "courses": False,
                "forum_posts": False,
            }
            | (brain_data.get("export") or {})
        ),
    )

    return Config(
        firecrawl_api_key=firecrawl_key,
        public_crawl=public_crawl,
        brain=brain,
        output=output,
        notes=notes,
    )
