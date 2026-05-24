"""Thin adapters between Streamlit pages and WeekPilot backend modules."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from weekpilot.collector import collect_inputs
from weekpilot.config import active_api_key, load_style, save_style
from weekpilot.models import PipelineResult, ReportConfig
from weekpilot.pipeline import run_generate
from weekpilot.privacy import sanitize_text
from weekpilot.utils import current_week_range, read_text


@dataclass(frozen=True)
class WeekRangeView:
    """Current reporting week for UI display."""

    start: date
    end: date
    week_id: str


@dataclass(frozen=True)
class InputFileView:
    """One input file row for UI display."""

    name: str
    label: str
    path: str
    exists: bool
    has_content: bool
    modified_at: datetime | None = None
    message: str = ''


@dataclass(frozen=True)
class InputStatusView:
    """Aggregated input readiness for UI display."""

    files: list[InputFileView]
    usable_file_count: int
    last_modified: datetime | None
    warnings: list[str] = field(default_factory=list)
    can_generate: bool = False
    disabled_reason: str | None = None


@dataclass(frozen=True)
class ModelStatusView:
    """Model and API-key readiness for UI display."""

    provider: str
    model: str
    base_url: str
    api_key_configured: bool
    api_key_tail: str | None
    key_source: str
    official_generation_available: bool
    disabled_reason: str | None = None
    last_test_status: str | None = None


@dataclass(frozen=True)
class PrivacyStatusView:
    """Privacy masking readiness for UI display."""

    enabled: bool
    detected_sensitive_count: int
    sensitive_types: list[str]
    blocking_issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConnectionTestResult:
    """Result of a lightweight model configuration check."""

    ok: bool
    message: str


@dataclass(frozen=True)
class RecentGenerationView:
    """Metadata for the latest generated output files."""

    exists: bool
    week_id: str = ''
    week_start: str = ''
    week_end: str = ''
    generated_at: datetime | None = None
    mode: str = ''
    model: str = ''
    quality_status: str = ''
    saved: bool = False


@dataclass(frozen=True)
class HistoryItemView:
    """One history entry summarized by week."""

    path: Path
    week_id: str
    week_start: str
    week_end: str
    generated_at: datetime | None
    mode: str
    model: str
    quality_status: str
    todo_count: int


@dataclass(frozen=True)
class SanitizedInputView:
    """Privacy-masked input preview for UI display."""

    weekly_log: str
    tasks_csv: str
    meeting_notes: str
    replacement_count: int
    replacement_labels: list[str]


INPUT_LABELS = {
    'weekly_log.md': '工作日志',
    'tasks.csv': '任务表',
    'meeting_notes.md': '会议纪要',
    'style.yaml': '报告风格',
}


def load_settings(style_path: str | Path) -> ReportConfig:
    """Load UI settings from style.yaml."""

    return load_style(style_path)


def save_settings(config: ReportConfig, style_path: str | Path) -> Path:
    """Persist UI settings to style.yaml."""

    return save_style(config, style_path)


def get_current_week_range(style: ReportConfig) -> WeekRangeView:
    """Return the current reporting week from style settings."""

    start, end, week_id = current_week_range(start_day=style.week_start_day, end_day=style.week_end_day)
    return WeekRangeView(start=start, end=end, week_id=week_id)


def get_input_status(input_dir: str | Path) -> InputStatusView:
    """Return input file readiness without exposing backend internals to pages."""

    collected = collect_inputs(input_dir)
    files: list[InputFileView] = []
    last_modified: datetime | None = None
    usable_file_count = 0

    for status in collected.file_statuses:
        target = Path(status.path)
        modified_at = datetime.fromtimestamp(target.stat().st_mtime) if target.exists() else None
        if modified_at and (last_modified is None or modified_at > last_modified):
            last_modified = modified_at
        has_content = bool(read_text(target).strip()) if target.exists() else False
        if status.name != 'style.yaml' and has_content:
            usable_file_count += 1
        files.append(
            InputFileView(
                name=status.name,
                label=INPUT_LABELS.get(status.name, status.name),
                path=str(target),
                exists=status.exists,
                has_content=has_content,
                modified_at=modified_at,
                message=status.message,
            )
        )

    can_generate = usable_file_count > 0
    disabled_reason = None if can_generate else '当前周暂无可用输入材料。请补充输入，或使用 Demo 模式体验流程。'
    return InputStatusView(
        files=files,
        usable_file_count=usable_file_count,
        last_modified=last_modified,
        warnings=collected.warnings,
        can_generate=can_generate,
        disabled_reason=disabled_reason,
    )


def get_model_status(root: str | Path, style: ReportConfig) -> ModelStatusView:
    """Return API key and model readiness for the UI."""

    key = active_api_key(root, style)
    provider = key.provider if key else style.llm.provider
    model = key.model if key else style.llm.model
    base_url = key.base_url if key else style.llm.base_url
    api_key_configured = bool(key and key.api_key)
    key_source = '未配置'
    if key:
        key_source = '环境变量' if key.name.startswith('env:') else f'本地配置：{key.name}'

    disabled_reason = None
    if not api_key_configured:
        disabled_reason = '未配置 API Key。正式周报生成不可用，可在设置页添加，或使用 Demo 模式。'

    return ModelStatusView(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key_configured=api_key_configured,
        api_key_tail=_mask_key_tail(key.api_key) if key else None,
        key_source=key_source,
        official_generation_available=api_key_configured,
        disabled_reason=disabled_reason,
    )


def get_privacy_status(input_dir: str | Path, style: ReportConfig) -> PrivacyStatusView:
    """Return current privacy masking status and a lightweight hit count."""

    settings = style.privacy
    enabled_types = []
    if settings.mask_emails:
        enabled_types.append('邮箱')
    if settings.mask_phone_numbers:
        enabled_types.append('联系方式')
    if settings.mask_urls:
        enabled_types.append('链接')
    if settings.mask_amounts:
        enabled_types.append('金额')
    if settings.custom_sensitive_terms or settings.forbidden_terms:
        enabled_types.append('自定义词表')

    if not settings.enabled:
        return PrivacyStatusView(enabled=False, detected_sensitive_count=0, sensitive_types=enabled_types)

    raw_text = '\n'.join(
        [
            read_text(Path(input_dir) / 'weekly_log.md'),
            read_text(Path(input_dir) / 'tasks.csv'),
            read_text(Path(input_dir) / 'meeting_notes.md'),
        ]
    )
    privacy = sanitize_text(raw_text, settings)
    detected_types = sorted({_placeholder_label(placeholder) for placeholder in privacy.replacements})
    return PrivacyStatusView(
        enabled=True,
        detected_sensitive_count=len(privacy.replacements),
        sensitive_types=detected_types or enabled_types,
    )


def get_sanitized_input_preview(input_dir: str | Path, style: ReportConfig) -> SanitizedInputView:
    """Return a per-file preview after local privacy masking."""

    root = Path(input_dir)
    files = {
        'weekly_log': read_text(root / 'weekly_log.md'),
        'tasks_csv': read_text(root / 'tasks.csv'),
        'meeting_notes': read_text(root / 'meeting_notes.md'),
    }
    masked: dict[str, str] = {}
    replacements: dict[str, str] = {}
    for key, text in files.items():
        privacy = sanitize_text(text, style.privacy)
        masked[key] = privacy.text
        replacements.update(privacy.replacements)
    labels = sorted({_placeholder_label(placeholder) for placeholder in replacements})
    return SanitizedInputView(
        weekly_log=masked['weekly_log'],
        tasks_csv=masked['tasks_csv'],
        meeting_notes=masked['meeting_notes'],
        replacement_count=len(replacements),
        replacement_labels=labels,
    )


def test_model_connection(root: str | Path, style: ReportConfig) -> ConnectionTestResult:
    """Run a local configuration check for model settings.

    This intentionally avoids a real paid/network LLM call in Phase 1.
    """

    status = get_model_status(root, style)
    if not status.api_key_configured:
        return ConnectionTestResult(ok=False, message='未配置 API Key，无法进行正式生成。')
    if not status.base_url.strip():
        return ConnectionTestResult(ok=False, message='Base URL 为空，请先补充模型服务地址。')
    return ConnectionTestResult(ok=True, message='本地配置校验通过。正式生成时会执行真实模型请求。')


def generate_report(root: str | Path, input_dir: str | Path, output_dir: str | Path, demo: bool) -> PipelineResult:
    """Generate a report with strict separation between formal and demo modes."""

    return run_generate(input_dir=input_dir, output_dir=output_dir, project_root=root, demo=demo)


def get_recent_generation(output_dir: str | Path) -> RecentGenerationView:
    """Read metadata for the latest generated output, if present."""

    root = Path(output_dir)
    meta_path = root / 'generation_meta.json'
    if not meta_path.exists():
        return RecentGenerationView(exists=False)

    try:
        payload = json.loads(meta_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return RecentGenerationView(
            exists=True,
            generated_at=datetime.fromtimestamp(meta_path.stat().st_mtime),
            quality_status='元信息读取失败',
        )

    meta = payload.get('report_meta', {})
    week_id = str(meta.get('week_id') or '')
    saved = bool(week_id and (root / 'history' / week_id).exists())
    return RecentGenerationView(
        exists=True,
        week_id=week_id,
        week_start=str(meta.get('week_start') or ''),
        week_end=str(meta.get('week_end') or ''),
        generated_at=datetime.fromtimestamp(meta_path.stat().st_mtime),
        mode=str(meta.get('llm_mode') or ''),
        model=str(meta.get('model') or ''),
        quality_status=_quality_status(root / 'report_quality.md'),
        saved=saved,
    )


def get_history_items(output_dir: str | Path) -> list[HistoryItemView]:
    """Return history entries summarized by week."""

    from weekpilot.history import list_history

    items: list[HistoryItemView] = []
    for path in list_history(output_dir):
        meta_path = path / 'generation_meta.json'
        meta = {}
        if meta_path.exists():
            try:
                payload = json.loads(meta_path.read_text(encoding='utf-8'))
                meta = payload.get('report_meta', {})
            except json.JSONDecodeError:
                meta = {}
        items.append(
            HistoryItemView(
                path=path,
                week_id=str(meta.get('week_id') or path.name),
                week_start=str(meta.get('week_start') or ''),
                week_end=str(meta.get('week_end') or ''),
                generated_at=datetime.fromtimestamp(meta_path.stat().st_mtime)
                if meta_path.exists()
                else None,
                mode=str(meta.get('llm_mode') or ''),
                model=str(meta.get('model') or ''),
                quality_status=_quality_status(path / 'report_quality.md'),
                todo_count=_todo_count(path / 'next_week_todo.md'),
            )
        )
    return items


def _mask_key_tail(api_key: str) -> str:
    if len(api_key) <= 4:
        return '****'
    return f'****{api_key[-4:]}'


def _placeholder_label(placeholder: str) -> str:
    stripped = placeholder.strip('[]')
    for suffix in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if stripped.endswith(suffix):
            return stripped[: -len(suffix)] or '敏感信息'
    while stripped and stripped[-1].isdigit():
        stripped = stripped[:-1]
    return stripped or '敏感信息'


def _quality_status(path: Path) -> str:
    content = read_text(path)
    if not content.strip():
        return '未检查'
    if '高优问题\n- 暂无高优问题' in content:
        return '通过，有建议'
    return '已检查'


def _todo_count(path: Path) -> int:
    content = read_text(path)
    return sum(1 for line in content.splitlines() if line.strip().startswith('- [ ]'))
