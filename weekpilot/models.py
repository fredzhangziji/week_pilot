"""Structured data models used across WeekPilot."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PrivacySettings(BaseModel):
    """Privacy settings used before model requests."""

    enabled: bool = True
    preview_before_send: bool = True
    masking_strategy: Literal['role_preserving', 'simple'] = 'role_preserving'
    forbidden_terms: list[str] = Field(default_factory=list)
    custom_sensitive_terms: list[str] = Field(default_factory=list)
    mask_emails: bool = True
    mask_phone_numbers: bool = True
    mask_urls: bool = True
    mask_amounts: bool = True


class LLMSettings(BaseModel):
    """Model settings stored in style.yaml and settings UI."""

    provider: str = 'openai'
    model: str = 'gpt-5.1-mini'
    base_url: str = 'https://api.openai.com/v1'
    active_key_name: str | None = None


class ReportConfig(BaseModel):
    """User-configurable report style settings."""

    report_type: Literal['weekly'] = 'weekly'
    language: str = 'zh-CN'
    audience: Literal['self', 'manager', 'team'] = 'manager'
    style: Literal['concise_professional', 'detailed_professional', 'retro'] = 'concise_professional'
    length: Literal['short', 'medium', 'long'] = 'medium'
    week_start_day: int = 0
    week_end_day: int = 4
    focus: list[str] = Field(default_factory=lambda: ['progress', 'deliverables', 'risks', 'next_week_plan'])
    output_versions: list[str] = Field(default_factory=lambda: ['standard', 'short', 'detailed', 'retro'])
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


class GeneratedReport(BaseModel):
    """All generated report artifacts."""

    standard: str
    short: str
    detailed: str
    retro: str
    quality_report: str = ''
    next_week_todo: str = ''
    llm_mode: Literal['formal', 'demo'] = 'formal'
    model: str = ''
    week_id: str = ''
    week_start: date | None = None
    week_end: date | None = None
    warnings: list[str] = Field(default_factory=list)


class FileStatus(BaseModel):
    """Input file state for UI and CLI diagnostics."""

    name: str
    path: str
    exists: bool
    required: bool = False
    message: str = ''


class CollectedInputs(BaseModel):
    """Raw file contents collected from the input directory."""

    input_dir: str
    weekly_log: str = ''
    tasks_csv: str = ''
    meeting_notes: str = ''
    style: ReportConfig = Field(default_factory=ReportConfig)
    file_statuses: list[FileStatus] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ApiKeyEntry(BaseModel):
    """A local API key entry. The secret should never be committed."""

    name: str
    provider: str = 'openai'
    api_key: str
    model: str = 'gpt-5.1-mini'
    base_url: str = 'https://api.openai.com/v1'
    is_active: bool = True


class ApiKeyStore(BaseModel):
    """Collection of locally configured API keys."""

    keys: list[ApiKeyEntry] = Field(default_factory=list)


class PrivacyResult(BaseModel):
    """Sanitized text plus local-only replacement map."""

    text: str
    replacements: dict[str, str] = Field(default_factory=dict)


class PromptBundle(BaseModel):
    """Prompt payload sent to the selected LLM provider."""

    developer_prompt: str
    user_prompt: str
    sanitized_user_prompt: str
    privacy: PrivacyResult = Field(default_factory=lambda: PrivacyResult(text=''))


class PipelineResult(BaseModel):
    """Return value for a generation run."""

    inputs: CollectedInputs
    report: GeneratedReport
    output_dir: str
    history_dir: str | None = None
    file_statuses: list[FileStatus] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    """Return a plain dict for Pydantic v2 models."""

    return model.model_dump(mode='json')
