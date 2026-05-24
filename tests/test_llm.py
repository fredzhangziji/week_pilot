"""LLM provider tests."""

import json

from weekpilot.llm import ChatCompletionsProvider, provider_from_key
from weekpilot.models import ApiKeyEntry


def test_deepseek_uses_chat_completions_provider():
    provider = provider_from_key(
        ApiKeyEntry(
            name='deepseek',
            provider='deepseek',
            api_key='test-key',
            model='deepseek-v4-flash',
            base_url='https://api.deepseek.com',
        )
    )

    assert isinstance(provider, ChatCompletionsProvider)
    assert provider.model == 'deepseek-v4-flash'


def test_chat_completions_provider_posts_expected_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps({'choices': [{'message': {'content': '{"standard": "ok"}'}}]}).encode('utf-8')

    def fake_urlopen(request, timeout):
        captured['url'] = request.full_url
        captured['timeout'] = timeout
        captured['payload'] = json.loads(request.data.decode('utf-8'))
        captured['authorization'] = request.headers['Authorization']
        return FakeResponse()

    monkeypatch.setattr('urllib.request.urlopen', fake_urlopen)
    provider = ChatCompletionsProvider(
        api_key='test-key',
        model='deepseek-v4-flash',
        base_url='https://api.deepseek.com',
        provider_name='deepseek',
    )

    text = provider.generate_text('system prompt', 'user prompt')

    assert captured['url'] == 'https://api.deepseek.com/chat/completions'
    assert captured['authorization'] == 'Bearer test-key'
    assert captured['payload']['model'] == 'deepseek-v4-flash'
    assert captured['payload']['messages'][0] == {'role': 'system', 'content': 'system prompt'}
    assert captured['payload']['messages'][1] == {'role': 'user', 'content': 'user prompt'}
    assert captured['payload']['response_format'] == {'type': 'json_object'}
    assert text == '{"standard": "ok"}'
