from __future__ import annotations

from pathlib import Path


def load_notes(input_dir: Path) -> list[dict[str, str]]:
    if not input_dir.exists():
        return []
    notes: list[dict[str, str]] = []
    for path in sorted(input_dir.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        notes.append(
            {
                "title": path.stem.replace("_", " ").title(),
                "path": str(path),
                "content": path.read_text(encoding="utf-8", errors="replace"),
            }
        )
    return notes
