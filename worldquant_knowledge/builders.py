from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from .markdown import now_utc, slugify, split_markdown_sections, write_markdown


PARTITIONS = {
    "operators": "Operators",
    "datasets_and_fields": "Datasets and Fields",
    "alpha_patterns": "Alpha Patterns",
    "public_articles": "Public Articles",
    "my_notes": "My Notes",
}


def build_sources(
    output_dir: Path,
    public_articles: list[dict[str, Any]],
    operators: list[dict[str, Any]],
    datasets: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    notes: list[dict[str, str]],
    max_words_per_file: int,
) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    updated_at = now_utc()
    _build_root_index(output_dir, updated_at)
    _build_operators(output_dir / "operators", operators, max_words_per_file, updated_at)
    _build_datasets_and_fields(output_dir / "datasets_and_fields", datasets, fields, max_words_per_file, updated_at)
    _build_alpha_patterns(output_dir / "alpha_patterns", updated_at)
    _build_public_articles(output_dir / "public_articles", public_articles, max_words_per_file, updated_at)
    _build_notes(output_dir / "my_notes", notes, max_words_per_file, updated_at)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["url", "title", "category", "status", "output_file", "error"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _build_root_index(output_dir: Path, updated_at: str) -> None:
    body = "\n".join(
        [
            "# WorldQuant Knowledge Base",
            "",
            "This source set is organized for a single NotebookLM notebook.",
            "",
            *[f"- `{name}/`: {title}" for name, title in PARTITIONS.items()],
        ]
    )
    write_markdown(
        output_dir / "00_index.md",
        _meta("WorldQuant Knowledge Base Index", "index", "generated", updated_at, ""),
        body,
    )


def _build_operators(path: Path, operators: list[dict[str, Any]], max_words: int, updated_at: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in operators:
        category = str(item.get("category") or item.get("type") or "overview")
        grouped.setdefault(slugify(category), []).append(item)
    _write_partition_index(path, "Operators", grouped.keys(), updated_at)
    if not grouped:
        _write_empty(path / "01_overview.md", "Operators Overview", "operators", updated_at)
        return
    for index, (group, items) in enumerate(sorted(grouped.items()), start=1):
        sections = [(f"## {_display_name(item, ['name', 'id'])}", _operator_body(item)) for item in items]
        _write_parts(path, f"{index:02d}_{group}", f"Operators - {group.replace('_', ' ').title()}", "operators", "brain_internal", "", sections, max_words, updated_at)


def _build_datasets_and_fields(
    path: Path,
    datasets: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    max_words: int,
    updated_at: str,
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_partition_index(path, "Datasets and Fields", ["datasets_overview", "fields"], updated_at)
    dataset_sections = [(f"## {_display_name(item, ['name', 'id'])}", _generic_body(item)) for item in datasets]
    _write_parts(path, "01_datasets_overview", "Datasets Overview", "datasets_and_fields", "brain_internal", "", dataset_sections, max_words, updated_at)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        dataset = field.get("dataset") if isinstance(field.get("dataset"), dict) else {}
        key = slugify(str(dataset.get("id") or field.get("datasetId") or field.get("category") or "other"))
        grouped.setdefault(key, []).append(field)
    for index, (group, items) in enumerate(sorted(grouped.items()), start=2):
        sections = [(f"## {_display_name(item, ['id', 'name'])}", _generic_body(item)) for item in items]
        _write_parts(path, f"{index:02d}_fields_{group}", f"Fields - {group}", "datasets_and_fields", "brain_internal", "", sections, max_words, updated_at)


def _build_alpha_patterns(path: Path, updated_at: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_partition_index(path, "Alpha Patterns", ["overview", "momentum", "reversal", "quality", "risk_neutralization", "turnover_control"], updated_at)
    body = (
        "# Alpha Patterns Overview\n\n"
        "This section is reserved for derived research patterns from public articles, operators, fields, and personal notes."
    )
    write_markdown(path / "01_overview.md", _meta("Alpha Patterns Overview", "alpha_patterns", "generated", updated_at, ""), body)


def _build_public_articles(path: Path, articles: list[dict[str, Any]], max_words: int, updated_at: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for article in articles:
        grouped.setdefault(str(article.get("category") or "worldquant"), []).append(article)
    _write_partition_index(path, "Public Articles", grouped.keys(), updated_at)
    for index, (group, items) in enumerate(sorted(grouped.items()), start=1):
        sections = [(f"## {item.get('title', 'Untitled')}\n\nSource: {item.get('url', '')}", str(item.get("markdown", ""))) for item in items]
        _write_parts(path, f"{index:02d}_{slugify(group)}", f"Public Articles - {group.replace('_', ' ').title()}", "public_articles", "firecrawl", "", sections, max_words, updated_at)


def _build_notes(path: Path, notes: list[dict[str, str]], max_words: int, updated_at: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_partition_index(path, "My Notes", [note["title"] for note in notes], updated_at)
    if not notes:
        return
    sections = [(f"## {note['title']}\n\nSource: {note['path']}", note["content"]) for note in notes]
    _write_parts(path, "01_my_notes", "My Notes", "my_notes", "local_notes", "", sections, max_words, updated_at)


def _write_partition_index(path: Path, title: str, entries: Any, updated_at: str) -> None:
    body = f"# {title}\n\nUpdated: {updated_at}\n\n" + "\n".join(f"- {entry}" for entry in entries)
    index_names = {
        "Operators": "00_operators_index.md",
        "Datasets and Fields": "00_datasets_fields_index.md",
        "Alpha Patterns": "00_alpha_patterns_index.md",
        "Public Articles": "00_public_articles_index.md",
        "My Notes": "00_my_notes_index.md",
    }
    index_name = index_names.get(title, f"00_{slugify(title)}_index.md")
    write_markdown(path / index_name, _meta(f"{title} Index", slugify(title), "generated", updated_at, ""), body)


def _write_parts(
    path: Path,
    stem: str,
    title: str,
    category: str,
    source_type: str,
    source_url: str,
    sections: list[tuple[str, str]],
    max_words: int,
    updated_at: str,
) -> None:
    parts = split_markdown_sections(sections, max_words)
    for index, body in enumerate(parts, start=1):
        suffix = "" if len(parts) == 1 else f"_part_{index}"
        write_markdown(
            path / f"{stem}{suffix}.md",
            _meta(title if len(parts) == 1 else f"{title} Part {index}", category, source_type, updated_at, source_url),
            body,
        )


def _write_empty(path: Path, title: str, category: str, updated_at: str) -> None:
    write_markdown(path, _meta(title, category, "generated", updated_at, ""), f"# {title}\n\nNo content exported.")


def _meta(title: str, category: str, source_type: str, updated_at: str, source_url: str) -> dict[str, object]:
    return {
        "title": title,
        "category": category,
        "source_type": source_type,
        "updated_at": updated_at,
        "source_url": source_url,
    }


def _display_name(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        if item.get(key):
            return str(item[key])
    return "Untitled"


def _operator_body(item: dict[str, Any]) -> str:
    return _generic_body(item)


def _generic_body(item: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in item.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        lines.append(f"- **{key}**: {rendered}")
    return "\n".join(lines)
