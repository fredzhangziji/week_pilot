"""Input collection for WeekPilot."""

from __future__ import annotations

from pathlib import Path

from weekpilot.config import load_style
from weekpilot.models import CollectedInputs, FileStatus
from weekpilot.utils import read_text

INPUT_FILES = {
    'weekly_log.md': {'required': False, 'label': '工作日志'},
    'tasks.csv': {'required': False, 'label': '任务表'},
    'meeting_notes.md': {'required': False, 'label': '会议纪要'},
    'style.yaml': {'required': False, 'label': '报告风格'},
}


def collect_inputs(input_dir: str | Path) -> CollectedInputs:
    """Read supported files from an input directory without crashing on misses."""

    root = Path(input_dir)
    statuses: list[FileStatus] = []
    warnings: list[str] = []

    for filename, meta in INPUT_FILES.items():
        target = root / filename
        exists = target.exists()
        if not exists:
            warnings.append(f'未找到 {filename}，将使用已有输入继续。')
        statuses.append(
            FileStatus(
                name=filename,
                path=str(target),
                exists=exists,
                required=meta['required'],
                message='已找到' if exists else '未找到',
            )
        )

    style = load_style(root / 'style.yaml')
    weekly_log = read_text(root / 'weekly_log.md')
    tasks_csv = read_text(root / 'tasks.csv')
    meeting_notes = read_text(root / 'meeting_notes.md')

    if not any([weekly_log.strip(), tasks_csv.strip(), meeting_notes.strip()]):
        warnings.append('没有读取到任何工作输入。可以先运行 sample 命令生成示例数据。')

    return CollectedInputs(
        input_dir=str(root),
        weekly_log=weekly_log,
        tasks_csv=tasks_csv,
        meeting_notes=meeting_notes,
        style=style,
        file_statuses=statuses,
        warnings=warnings,
    )
