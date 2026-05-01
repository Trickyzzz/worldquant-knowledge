from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from worldquant_knowledge.config import ConfigError, load_config
from worldquant_knowledge.pipeline import build_all, run_brain, run_notes, run_public


def main() -> int:
    parser = argparse.ArgumentParser(description="Build WorldQuant NotebookLM markdown sources.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--all", action="store_true", help="Run public, brain, notes, and build")
    parser.add_argument("--public", action="store_true", help="Fetch public WorldQuant content")
    parser.add_argument("--brain", action="store_true", help="Export BRAIN structured data")
    parser.add_argument("--notes", action="store_true", help="Load local notes")
    parser.add_argument("--build", action="store_true", help="Build markdown from cached raw files")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        public_articles: list[dict] = []
        operators: list[dict] = []
        datasets: list[dict] = []
        fields: list[dict] = []
        notes: list[dict[str, str]] = []

        run_everything = args.all or not any([args.public, args.brain, args.notes, args.build])
        if run_everything or args.public:
            public_articles = run_public(config)
        if run_everything or args.brain:
            operators, datasets, fields = run_brain(config)
        if run_everything or args.notes:
            notes = run_notes(config)
        if args.build and not run_everything:
            public_articles = _read_json(config.output.raw_dir / "public_articles.json", [])
            operators = _read_json(config.output.raw_dir / "brain" / "operators.json", [])
            datasets = _read_json(config.output.raw_dir / "brain" / "datasets.json", [])
            fields = _read_json(config.output.raw_dir / "brain" / "fields.json", [])
            notes = run_notes(config)
        if run_everything or args.build:
            build_all(config, public_articles, operators, datasets, fields, notes)
        print(f"Generated sources in {config.output.dir}")
        return 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1


def _read_json(path: Path, default: list[dict]) -> list[dict]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
