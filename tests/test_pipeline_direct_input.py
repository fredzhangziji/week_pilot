"""Pipeline tests for direct-input report generation."""

import json

from weekpilot.llm import LLMProvider
from weekpilot.pipeline import run_generate
from weekpilot.utils import write_text


class CapturingProvider(LLMProvider):
    mode = 'formal'
    model = 'capture-model'

    def __init__(self):
        self.user_prompt = ''

    def generate_text(self, developer_prompt: str, user_prompt: str) -> str:
        self.user_prompt = user_prompt
        return json.dumps(
            {
                'standard': '## 本周工作进展\n- ok',
                'short': 'ok',
                'detailed': 'ok',
                'retro': 'ok',
                'next_week_todo': '- [ ] ok',
            },
            ensure_ascii=False,
        )


def test_pipeline_sends_sanitized_raw_inputs_without_extraction(tmp_path):
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    write_text(input_dir / 'weekly_log.md', '# Weekly Log\n\n- 完成 Alpha 项目同步，联系人 a@example.com。')
    write_text(input_dir / 'tasks.csv', 'task,status,priority,due_date,note\n补充材料,todo,P1,2026-05-24,\n')
    provider = CapturingProvider()

    result = run_generate(input_dir=input_dir, output_dir=output_dir, project_root=tmp_path, provider=provider)

    assert result.report.next_week_todo == '- [ ] ok'
    assert 'weekly_log.md:' in provider.user_prompt
    assert '完成 Alpha 项目同步' in provider.user_prompt
    assert 'a@example.com' not in provider.user_prompt
    assert '邮箱A' in provider.user_prompt


def test_pipeline_demo_uses_sample_data_instead_of_real_input(tmp_path):
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    write_text(input_dir / 'weekly_log.md', '# Weekly Log\n\n- 真实输入不应进入 Demo。')

    result = run_generate(input_dir=input_dir, output_dir=output_dir, project_root=tmp_path, demo=True)

    combined = '\n'.join([result.report.standard, result.report.short, result.report.detailed, result.report.retro])
    assert result.report.llm_mode == 'demo'
    assert '演示模式' in combined
    assert '完成本地环境配置' in combined
    assert '真实输入不应进入 Demo' not in combined
