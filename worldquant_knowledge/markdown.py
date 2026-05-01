from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def frontmatter(values: dict[str, object]) -> str:
    lines = ["---"]
    for key, raw_value in values.items():
        value = "" if raw_value is None else str(raw_value)
        value = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}: "{value}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


def split_markdown_sections(sections: Iterable[tuple[str, str]], max_words: int) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    current_words = 0

    for heading, body in sections:
        block = f"{heading}\n\n{body.strip()}\n".strip() + "\n"
        block_words = word_count(block)
        if current and current_words + block_words > max_words:
            parts.append("\n".join(current).strip() + "\n")
            current = []
            current_words = 0
        current.append(block)
        current_words += block_words

    if current:
        parts.append("\n".join(current).strip() + "\n")
    return parts or [""]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "untitled"


def write_markdown(path: Path, metadata: dict[str, object], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter(metadata) + "\n" + body.strip() + "\n", encoding="utf-8")
