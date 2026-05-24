"""Configuration loading and local API key management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from weekpilot.models import ApiKeyEntry, ApiKeyStore, ReportConfig, model_to_dict
from weekpilot.utils import ensure_dir, write_text

DEFAULT_STYLE: dict[str, Any] = {
    'report_type': 'weekly',
    'language': 'zh-CN',
    'audience': 'manager',
    'style': 'concise_professional',
    'length': 'medium',
    'week_start_day': 0,
    'week_end_day': 4,
    'focus': ['progress', 'deliverables', 'risks', 'next_week_plan'],
    'output_versions': ['standard', 'short', 'detailed', 'retro'],
    'privacy': {
        'enabled': True,
        'preview_before_send': True,
        'masking_strategy': 'role_preserving',
        'forbidden_terms': [],
        'custom_sensitive_terms': [],
        'mask_emails': True,
        'mask_phone_numbers': True,
        'mask_urls': True,
        'mask_amounts': True,
    },
    'llm': {
        'provider': 'openai',
        'model': 'gpt-5.5',
        'base_url': 'https://api.openai.com/v1',
        'active_key_name': None,
    },
}


def project_root_from(path: str | Path | None = None) -> Path:
    """Resolve the project root from an optional path."""

    return Path(path or Path.cwd()).resolve()


def load_environment(root: str | Path | None = None) -> None:
    """Load .env from the project root if it exists."""

    project_root = project_root_from(root)
    load_dotenv(project_root / '.env')


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge nested dictionaries without mutating either input."""

    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_style(style_path: str | Path) -> ReportConfig:
    """Load style.yaml, falling back to default values."""

    target = Path(style_path)
    if not target.exists():
        return ReportConfig(**DEFAULT_STYLE)
    raw = yaml.safe_load(target.read_text(encoding='utf-8')) or {}
    return ReportConfig(**deep_merge(DEFAULT_STYLE, raw))


def save_style(config: ReportConfig, style_path: str | Path) -> Path:
    """Persist report style settings as YAML."""

    data = model_to_dict(config)
    content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    return write_text(style_path, content)


def api_key_store_path(root: str | Path) -> Path:
    """Return the ignored local API key store path."""

    return Path(root) / 'config' / 'api_keys.yaml'


def load_api_key_store(root: str | Path) -> ApiKeyStore:
    """Load configured local API keys."""

    target = api_key_store_path(root)
    if not target.exists():
        return ApiKeyStore()
    raw = yaml.safe_load(target.read_text(encoding='utf-8')) or {}
    return ApiKeyStore(**raw)


def save_api_key_store(root: str | Path, store: ApiKeyStore) -> Path:
    """Save configured API keys to the ignored local key store."""

    target = api_key_store_path(root)
    ensure_dir(target.parent)
    content = yaml.safe_dump(model_to_dict(store), allow_unicode=True, sort_keys=False)
    return write_text(target, content)


def upsert_api_key(root: str | Path, entry: ApiKeyEntry) -> ApiKeyStore:
    """Create or update one local API key entry."""

    store = load_api_key_store(root)
    keys = [key for key in store.keys if key.name != entry.name]
    if entry.is_active:
        keys = [key.model_copy(update={'is_active': False}) for key in keys]
    keys.append(entry)
    updated = ApiKeyStore(keys=keys)
    save_api_key_store(root, updated)
    return updated


def active_api_key(root: str | Path, style: ReportConfig | None = None) -> ApiKeyEntry | None:
    """Return the selected API key entry, checking config first and .env second."""

    load_environment(root)
    store = load_api_key_store(root)
    preferred_name = style.llm.active_key_name if style else None
    if preferred_name:
        for key in store.keys:
            if key.name == preferred_name and key.api_key:
                return key
    for key in store.keys:
        if key.is_active and key.api_key:
            return key
    style_provider = (style.llm.provider if style else 'openai').lower()
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    if style_provider == 'deepseek' and deepseek_key:
        return ApiKeyEntry(
            name='env:DEEPSEEK_API_KEY',
            provider='deepseek',
            api_key=deepseek_key,
            model=os.getenv('DEEPSEEK_MODEL') or (style.llm.model if style else 'deepseek-v4-flash'),
            base_url=os.getenv('DEEPSEEK_BASE_URL') or (style.llm.base_url if style else 'https://api.deepseek.com'),
            is_active=True,
        )
    if openai_key:
        return ApiKeyEntry(
            name='env:OPENAI_API_KEY',
            provider=os.getenv('OPENAI_PROVIDER', 'openai'),
            api_key=openai_key,
            model=os.getenv('OPENAI_MODEL') or (style.llm.model if style else 'gpt-5.5'),
            base_url=os.getenv('OPENAI_BASE_URL') or (style.llm.base_url if style else 'https://api.openai.com/v1'),
            is_active=True,
        )
    if deepseek_key:
        return ApiKeyEntry(
            name='env:DEEPSEEK_API_KEY',
            provider='deepseek',
            api_key=deepseek_key,
            model=os.getenv('DEEPSEEK_MODEL') or 'deepseek-v4-flash',
            base_url=os.getenv('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com',
            is_active=True,
        )
    return None


def has_active_api_key(root: str | Path, style: ReportConfig | None = None) -> bool:
    """Return True when a usable API key exists."""

    return active_api_key(root, style) is not None
