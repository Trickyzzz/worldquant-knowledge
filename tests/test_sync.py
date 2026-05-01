import json

import sync
from worldquant_knowledge.config import BrainConfig, Config, NotesConfig, OutputConfig, PublicCrawlConfig


def test_incremental_all_uses_cached_raw_data(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    (raw_dir / "brain").mkdir(parents=True)
    (raw_dir / "public_articles.json").write_text(
        json.dumps([{"title": "Article", "url": "https://example.com", "markdown": "momentum", "category": "worldquant"}]),
        encoding="utf-8",
    )
    (raw_dir / "brain" / "operators.json").write_text(
        json.dumps([{"name": "ts_delta", "description": "momentum"}]),
        encoding="utf-8",
    )
    (raw_dir / "brain" / "datasets.json").write_text(json.dumps([{"id": "pv1"}]), encoding="utf-8")
    (raw_dir / "brain" / "fields.json").write_text(json.dumps([{"id": "close"}]), encoding="utf-8")

    config = Config(
        firecrawl_api_key="fc-test",
        public_crawl=PublicCrawlConfig(),
        brain=BrainConfig(cookie="session=abc"),
        output=OutputConfig(dir=tmp_path / "out", raw_dir=raw_dir),
        notes=NotesConfig(enabled=False),
    )
    calls = {"public": 0, "brain": 0, "build": 0}

    monkeypatch.setattr(sync, "load_config", lambda _: config)
    monkeypatch.setattr(sync, "run_public", lambda _: calls.__setitem__("public", calls["public"] + 1))
    monkeypatch.setattr(sync, "run_brain", lambda _: calls.__setitem__("brain", calls["brain"] + 1))
    monkeypatch.setattr(
        sync,
        "build_all",
        lambda config, public, operators, datasets, fields, notes: calls.__setitem__("build", calls["build"] + 1),
    )
    monkeypatch.setattr(sync.sys, "argv", ["sync.py", "--all", "--incremental", "--config", "config.yaml"])

    assert sync.main() == 0
    assert calls == {"public": 0, "brain": 0, "build": 1}
