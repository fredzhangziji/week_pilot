"""Filesystem-backed history for generated weekly reports."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from weekpilot.models import GeneratedReport, ReportConfig
from weekpilot.utils import current_week_range, ensure_dir

HISTORY_FILES = (
    'generation_meta.json',
    'weekly_report.md',
    'weekly_report_short.md',
    'weekly_report_detailed.md',
    'weekly_retro.md',
    'report_quality.md',
    'next_week_todo.md',
)


def apply_week_metadata(report: GeneratedReport, config: ReportConfig, today: date | None = None) -> GeneratedReport:
    """Attach week range metadata to a report."""

    start, end, week_id = current_week_range(today=today, start_day=config.week_start_day, end_day=config.week_end_day)
    return report.model_copy(update={'week_id': week_id, 'week_start': start, 'week_end': end})


def save_history(output_dir: str | Path, report: GeneratedReport) -> Path:
    """Copy current output artifacts into output/history/<week_id>."""

    root = Path(output_dir)
    week_id = report.week_id or current_week_range()[2]
    history_dir = ensure_dir(root / 'history' / week_id)
    for filename in HISTORY_FILES:
        source = root / filename
        if source.exists():
            shutil.copy2(source, history_dir / filename)
    return history_dir


def list_history(output_dir: str | Path) -> list[Path]:
    """List generated history directories newest first."""

    history_root = Path(output_dir) / 'history'
    if not history_root.exists():
        return []
    return sorted([path for path in history_root.iterdir() if path.is_dir()], reverse=True)
