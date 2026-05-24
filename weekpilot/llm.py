"""LLM providers for WeekPilot."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from weekpilot.config import active_api_key
from weekpilot.models import ApiKeyEntry, CollectedInputs, ReportConfig


class MissingAPIKeyError(RuntimeError):
    """Raised when a formal LLM request is attempted without an API key."""


class LLMProvider(ABC):
    """Minimal interface used by the summarizer."""

    mode: str
    model: str

    @abstractmethod
    def generate_text(self, developer_prompt: str, user_prompt: str) -> str:
        """Generate text from a prompt pair."""


@dataclass
class OpenAIResponsesProvider(LLMProvider):
    """OpenAI Responses API provider implemented with the standard library."""

    api_key: str
    model: str
    base_url: str = 'https://api.openai.com/v1'
    timeout_seconds: int = 90
    mode: str = 'formal'

    def generate_text(self, developer_prompt: str, user_prompt: str) -> str:
        endpoint = f'{self.base_url.rstrip("/")}/responses'
        payload = {
            'model': self.model,
            'instructions': developer_prompt,
            'input': user_prompt,
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'LLM API 请求失败：HTTP {exc.code} {body[:500]}') from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f'LLM API 请求失败：{exc.reason}') from exc
        return _extract_response_text(data)


@dataclass
class ChatCompletionsProvider(LLMProvider):
    """OpenAI-compatible chat completions provider."""

    api_key: str
    model: str
    base_url: str
    provider_name: str = 'openai-compatible'
    timeout_seconds: int = 90
    mode: str = 'formal'

    def generate_text(self, developer_prompt: str, user_prompt: str) -> str:
        endpoint = f'{self.base_url.rstrip("/")}/chat/completions'
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': developer_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.2,
            'response_format': {'type': 'json_object'},
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'LLM API 请求失败：HTTP {exc.code} {body[:500]}') from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f'LLM API 请求失败：{exc.reason}') from exc
        return _extract_chat_completion_text(data)


class DemoLLMProvider(LLMProvider):
    """Deterministic local demo provider used for tests and no-key previews."""

    mode = 'demo'
    model = 'weekpilot-demo-provider'

    def __init__(self, inputs: CollectedInputs | None = None):
        self.inputs = inputs

    def generate_text(self, developer_prompt: str, user_prompt: str) -> str:
        from weekpilot.summarizer import render_template_reports_from_inputs

        if self.inputs:
            reports = render_template_reports_from_inputs(self.inputs, demo=True)
            return json.dumps(reports, ensure_ascii=False)
        payload = {
            'standard': '## 本周工作进展\n- 演示模式：未提供输入。',
            'short': '演示模式：未提供输入。',
            'detailed': '## 本周工作进展\n- 演示模式：未提供输入。',
            'retro': '## 个人复盘\n- 演示模式：未提供输入。',
            'next_week_todo': '- [ ] 待补充下周计划',
        }
        return json.dumps(payload, ensure_ascii=False)


def provider_from_config(
    root: str,
    config: ReportConfig,
    allow_demo: bool = False,
) -> LLMProvider:
    """Resolve the provider to use for this run."""

    key_entry = active_api_key(root, config)
    if key_entry:
        return provider_from_key(key_entry)
    if allow_demo:
        return DemoLLMProvider()
    raise MissingAPIKeyError('未配置 API Key。请在设置页添加 API Key，或在 CLI 中使用 --demo 查看演示输出。')


def provider_from_key(entry: ApiKeyEntry) -> LLMProvider:
    """Build a provider from a local key entry."""

    provider = entry.provider.strip().lower()
    if provider == 'openai':
        return OpenAIResponsesProvider(api_key=entry.api_key, model=entry.model, base_url=entry.base_url)
    if provider in {'deepseek', 'openai-compatible', 'openai_chat'}:
        return ChatCompletionsProvider(
            api_key=entry.api_key,
            model=entry.model,
            base_url=entry.base_url,
            provider_name=provider,
        )
    raise ValueError(f'暂不支持的 provider：{entry.provider}')


def _extract_response_text(data: dict[str, Any]) -> str:
    if isinstance(data.get('output_text'), str):
        return data['output_text']
    output = data.get('output', [])
    chunks: list[str] = []
    for item in output:
        for content in item.get('content', []):
            text = content.get('text')
            if text:
                chunks.append(text)
    if chunks:
        return '\n'.join(chunks)
    return json.dumps(data, ensure_ascii=False)


def _extract_chat_completion_text(data: dict[str, Any]) -> str:
    choices = data.get('choices') or []
    if choices:
        message = choices[0].get('message') or {}
        content = message.get('content')
        if isinstance(content, str) and content:
            return content
    return json.dumps(data, ensure_ascii=False)
