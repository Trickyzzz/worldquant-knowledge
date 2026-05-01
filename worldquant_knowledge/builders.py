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
    _build_alpha_patterns(output_dir / "alpha_patterns", operators, fields, public_articles, notes, updated_at)
    if public_articles:
        _build_public_articles(output_dir / "public_articles", public_articles, max_words_per_file, updated_at)
    if notes:
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


def _build_alpha_patterns(
    path: Path,
    operators: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    public_articles: list[dict[str, Any]],
    notes: list[dict[str, str]],
    updated_at: str,
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    patterns = [
        ("01_overview.md", "Alpha Patterns Overview", "overview", []),
        ("02_momentum.md", "Momentum Alpha Patterns", "momentum", ["momentum", "trend", "delta", "ts_delta", "ts_rank", "relative performance"]),
        ("03_reversal.md", "Reversal Alpha Patterns", "reversal", ["reversal", "mean reversion", "contrarian", "zscore", "ts_zscore"]),
        ("04_quality.md", "Quality Alpha Patterns", "quality", ["quality", "fundamental", "earnings", "profit", "margin", "debt"]),
        ("05_risk_neutralization.md", "Risk Neutralization Alpha Patterns", "risk_neutralization", ["neutralization", "neutralize", "group", "sector", "industry", "risk"]),
        ("06_turnover_control.md", "Turnover Control Alpha Patterns", "turnover_control", ["turnover", "decay", "hump", "trade_when", "liquidity", "volume"]),
    ]
    written_slugs: list[str] = []
    for filename, title, slug, keywords in patterns:
        body = _alpha_pattern_body(title, slug, keywords, operators, fields, public_articles, notes)
        if body is None:
            continue
        write_markdown(path / filename, _meta(title, "alpha_patterns", "derived_from_sources", updated_at, ""), body)
        written_slugs.append(slug)
    _write_partition_index(path, "Alpha Patterns", written_slugs, updated_at)


def _alpha_pattern_body(
    title: str,
    slug: str,
    keywords: list[str],
    operators: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    public_articles: list[dict[str, Any]],
    notes: list[dict[str, str]],
) -> str | None:
    if slug == "overview":
        return _alpha_overview_body(operators, fields, public_articles, notes)

    matched_operators = _match_items(operators, keywords)
    matched_fields = _match_items(fields, keywords)
    matched_articles = _match_articles(public_articles, keywords)
    matched_notes = _match_notes(notes, keywords)
    if not any([matched_operators, matched_fields, matched_articles, matched_notes]):
        return None

    lines = [
        f"# {title}",
        "",
        "This file is derived from the currently exported WorldQuant sources.",
    ]
    if matched_operators:
        lines.extend(["", "## Matching Operators", "", _render_named_items(matched_operators, ["name", "id"], limit=40)])
    if matched_fields:
        lines.extend(["", "## Matching Fields", "", _render_named_items(matched_fields, ["id", "name"], limit=80)])
    if matched_articles:
        lines.extend(["", "## Matching Public Articles", "", _render_articles(matched_articles)])
    if matched_notes:
        lines.extend(["", "## Matching Notes", "", _render_notes(matched_notes)])
    return "\n".join(lines)


def _alpha_overview_body(
    operators: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    public_articles: list[dict[str, Any]],
    notes: list[dict[str, str]],
) -> str:
    return "\n".join(
        [
            "# Alpha Patterns Overview",
            "",
            "This section is derived from exported WorldQuant sources and local notes.",
            "",
            f"- Operators exported: {len(operators)}",
            f"- Fields exported: {len(fields)}",
            f"- Public articles exported: {len(public_articles)}",
            f"- Local notes loaded: {len(notes)}",
            "",
            "Pattern files group matching source material by keywords so NotebookLM can retrieve related operators, fields, articles, and notes together.",
        ]
    )


def _match_items(items: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    return [item for item in items if _contains_keyword(json.dumps(item, ensure_ascii=False), keywords)]


def _match_articles(articles: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    return [
        article
        for article in articles
        if _contains_keyword(f"{article.get('title', '')}\n{article.get('markdown', '')}", keywords)
    ]


def _match_notes(notes: list[dict[str, str]], keywords: list[str]) -> list[dict[str, str]]:
    return [note for note in notes if _contains_keyword(f"{note.get('title', '')}\n{note.get('content', '')}", keywords)]


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _render_named_items(items: list[dict[str, Any]], name_keys: list[str], limit: int) -> str:
    if not items:
        return "No matching exported source items found."
    lines: list[str] = []
    for item in items[:limit]:
        name = _display_name(item, name_keys)
        description = str(item.get("description") or item.get("definition") or item.get("category") or "").strip()
        lines.append(f"- **{name}**: {description}" if description else f"- **{name}**")
    if len(items) > limit:
        lines.append(f"- ...and {len(items) - limit} more matching items.")
    return "\n".join(lines)


def _render_articles(articles: list[dict[str, Any]]) -> str:
    if not articles:
        return "No matching public articles found."
    return "\n".join(f"- **{article.get('title', 'Untitled')}**: {article.get('url', '')}" for article in articles[:30])


def _render_notes(notes: list[dict[str, str]]) -> str:
    if not notes:
        return "No matching local notes found."
    return "\n".join(f"- **{note.get('title', 'Untitled')}**: {note.get('path', '')}" for note in notes[:30])


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
