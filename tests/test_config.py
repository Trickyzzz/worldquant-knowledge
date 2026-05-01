from pathlib import Path

import pytest

from worldquant_knowledge.config import ConfigError, load_config


def test_load_config_reads_required_secret_files(tmp_path, monkeypatch):
    api_key_file = tmp_path / "firecrawl.txt"
    cookie_file = tmp_path / "cookie.txt"
    api_key_file.write_text("fc-test\n", encoding="utf-8")
    cookie_file.write_text("session=abc", encoding="utf-8")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
firecrawl_api_key_file: "{api_key_file.as_posix()}"
public_crawl:
  enabled: true
  seed_urls:
    - "https://www.worldquant.com/"
brain:
  enabled: true
  cookie_file: "{cookie_file.as_posix()}"
  max_rate_limit_retries: 9
  rate_limit_backoff_seconds: 30
  max_rate_limit_sleep_seconds: 300
output:
  dir: "{(tmp_path / 'out').as_posix()}"
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.firecrawl_api_key == "fc-test"
    assert config.brain.cookie == "session=abc"
    assert config.brain.max_rate_limit_retries == 9
    assert config.brain.rate_limit_backoff_seconds == 30
    assert config.brain.max_rate_limit_sleep_seconds == 300
    assert config.public_crawl.seed_urls == ["https://www.worldquant.com/"]


def test_load_config_fails_when_firecrawl_key_is_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    cookie_file = tmp_path / "cookie.txt"
    cookie_file.write_text("session=abc", encoding="utf-8")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
public_crawl:
  enabled: true
  seed_urls:
    - "https://www.worldquant.com/"
brain:
  enabled: false
  cookie_file: "{cookie_file.as_posix()}"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Firecrawl"):
        load_config(config_file)


def test_load_config_fails_when_brain_cookie_is_missing(tmp_path):
    api_key_file = tmp_path / "firecrawl.txt"
    api_key_file.write_text("fc-test", encoding="utf-8")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
firecrawl_api_key_file: "{api_key_file.as_posix()}"
public_crawl:
  enabled: true
  seed_urls:
    - "https://www.worldquant.com/"
brain:
  enabled: true
  cookie_file: "{(tmp_path / 'missing-cookie.txt').as_posix()}"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="cookie"):
        load_config(config_file)
