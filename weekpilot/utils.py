"""Small utility helpers."""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""

    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def read_text(path: str | Path) -> str:
    """Read UTF-8 text, returning an empty string for missing files."""

    target = Path(path)
    if not target.exists():
        return ''
    return target.read_text(encoding='utf-8')


def write_text(path: str | Path, content: str) -> Path:
    """Write UTF-8 text, creating parent directories if needed."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
    return target


def clean_bullet(line: str) -> str:
    """Normalize markdown list prefixes and weekday labels."""

    text = line.strip()
    text = re.sub(r'^\s*[-*+]\s*', '', text)
    text = re.sub(r'^\s*\d+[.)]\s*', '', text)
    text = re.sub(r'^(周[一二三四五六日天]|星期[一二三四五六日天])[:：]\s*', '', text)
    return text.strip()


def split_meaningful_lines(text: str) -> list[tuple[int, str]]:
    """Return non-empty markdown lines that carry content."""

    lines: list[tuple[int, str]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        cleaned = clean_bullet(line)
        if not cleaned or cleaned.startswith('#'):
            continue
        lines.append((index, cleaned))
    return lines


def normalize_title(value: str) -> str:
    """Normalize a title for de-duplication."""

    return re.sub(r'\s+', '', value.strip().lower())


def current_week_range(today: date | None = None, start_day: int = 0, end_day: int = 4) -> tuple[date, date, str]:
    """Return the current week range and ISO week id.

    Weekday follows Python's convention: Monday is 0 and Sunday is 6.
    """

    base = today or date.today()
    start = base - timedelta(days=(base.weekday() - start_day) % 7)
    end = start + timedelta(days=(end_day - start_day) % 7)
    iso = start.isocalendar()
    return start, end, f'{iso.year}-W{iso.week:02d}'


def markdown_list(items: list[str], empty: str = '暂无明确记录。') -> str:
    """Render a markdown bullet list."""

    if not items:
        return f'- {empty}'
    return '\n'.join(f'- {item}' for item in items)
