"""Local privacy masking before sending prompts to an LLM."""

from __future__ import annotations

import re

from weekpilot.models import PrivacyResult, PrivacySettings

EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
PHONE_PATTERN = re.compile(r'(?<!\d)(?:\+?\d[\d\s-]{7,}\d)(?!\d)')
URL_PATTERN = re.compile(r'https?://[^\s)]+')
AMOUNT_PATTERN = re.compile(r'(?<!\w)(?:\d+(?:\.\d+)?\s*(?:元|万元|人民币|USD|美元))(?!\w)')


def sanitize_text(text: str, settings: PrivacySettings) -> PrivacyResult:
    """Mask configured sensitive terms and common sensitive formats."""

    if not settings.enabled or not text:
        return PrivacyResult(text=text)

    replacements: dict[str, str] = {}
    masked = text

    for index, term in enumerate(_unique_terms(settings), start=1):
        placeholder = _placeholder('敏感词', index, settings)
        masked = masked.replace(term, placeholder)
        replacements[placeholder] = term

    pattern_specs: list[tuple[bool, re.Pattern[str], str]] = [
        (settings.mask_emails, EMAIL_PATTERN, '邮箱'),
        (settings.mask_phone_numbers, PHONE_PATTERN, '联系方式'),
        (settings.mask_urls, URL_PATTERN, '链接'),
        (settings.mask_amounts, AMOUNT_PATTERN, '金额数据'),
    ]
    for enabled, pattern, label in pattern_specs:
        if not enabled:
            continue
        matches = list(dict.fromkeys(pattern.findall(masked)))
        for index, match in enumerate(matches, start=1):
            placeholder = _placeholder(label, index, settings)
            masked = masked.replace(match, placeholder)
            replacements[placeholder] = match

    return PrivacyResult(text=masked, replacements=replacements)


def _unique_terms(settings: PrivacySettings) -> list[str]:
    terms = [term.strip() for term in [*settings.forbidden_terms, *settings.custom_sensitive_terms]]
    return [term for term in dict.fromkeys(terms) if term]


def _placeholder(label: str, index: int, settings: PrivacySettings) -> str:
    if settings.masking_strategy == 'simple':
        return f'[{label}{index}]'
    return f'{label}{chr(64 + min(index, 26))}'
