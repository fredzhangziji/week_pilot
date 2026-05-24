"""Export generated WeekPilot artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from weekpilot.models import CollectedInputs, GeneratedReport, model_to_dict
from weekpilot.utils import ensure_dir, write_text


def export_outputs(inputs: CollectedInputs, report: GeneratedReport, output_dir: str | Path) -> dict[str, Path]:
    """Write all MVP output files."""

    root = ensure_dir(output_dir)
    paths = {
        'generation_meta': root / 'generation_meta.json',
        'weekly_report': root / 'weekly_report.md',
        'weekly_report_short': root / 'weekly_report_short.md',
        'weekly_report_detailed': root / 'weekly_report_detailed.md',
        'weekly_retro': root / 'weekly_retro.md',
        'report_quality': root / 'report_quality.md',
        'next_week_todo': root / 'next_week_todo.md',
    }
    structured = {
        'input_meta': {
            'input_dir': inputs.input_dir,
            'files': [model_to_dict(status) for status in inputs.file_statuses],
            'warnings': inputs.warnings,
        },
        'report_meta': {
            'llm_mode': report.llm_mode,
            'model': report.model,
            'week_id': report.week_id,
            'week_start': report.week_start.isoformat() if report.week_start else None,
            'week_end': report.week_end.isoformat() if report.week_end else None,
            'warnings': report.warnings,
        },
    }
    write_text(paths['generation_meta'], json.dumps(structured, ensure_ascii=False, indent=2))
    write_text(paths['weekly_report'], report.standard)
    write_text(paths['weekly_report_short'], report.short)
    write_text(paths['weekly_report_detailed'], report.detailed)
    write_text(paths['weekly_retro'], report.retro)
    write_text(paths['report_quality'], report.quality_report)
    write_text(paths['next_week_todo'], report.next_week_todo)
    return paths
