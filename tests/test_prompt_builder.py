"""Prompt builder tests."""

from weekpilot.collector import collect_inputs
from weekpilot.prompt_builder import build_prompt_from_inputs
from weekpilot.utils import write_text


def test_prompt_builder_includes_schema_source_guidance_and_sanitizes(tmp_path):
    input_dir = tmp_path / 'input'
    write_text(input_dir / 'weekly_log.md', '- 完成接口联调，联系人 owner@example.com。')
    inputs = collect_inputs(input_dir)

    prompt = build_prompt_from_inputs(inputs)

    assert '"standard"' in prompt.user_prompt
    assert '"next_week_todo"' in prompt.user_prompt
    assert '输入来源说明' in prompt.user_prompt
    assert '表达优化目标' in prompt.user_prompt
    assert '润色与扩写边界' in prompt.user_prompt
    assert '合理的价值提炼' in prompt.developer_prompt
    assert '动作 + 对象 + 结果' in prompt.user_prompt
    assert 'weekly_log.md:' in prompt.sanitized_user_prompt
    assert 'owner@example.com' not in prompt.sanitized_user_prompt
    assert '邮箱A' in prompt.sanitized_user_prompt
