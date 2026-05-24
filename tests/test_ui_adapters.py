"""UI adapter tests."""

from weekpilot.ui.adapters import generate_report
from weekpilot.utils import write_text


def test_demo_generation_uses_sample_data_instead_of_real_input(tmp_path):
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    write_text(input_dir / 'weekly_log.md', '# Weekly Log\n\n- 完成真实项目事项，Demo 模式不应读取。\n')
    write_text(input_dir / 'tasks.csv', 'task,status,priority,due_date,note\n真实任务,done,P1,2026-05-24,\n')

    result = generate_report(root=tmp_path, input_dir=input_dir, output_dir=output_dir, demo=True)

    combined = '\n'.join([result.report.standard, result.report.short, result.report.detailed, result.report.retro])
    assert result.report.llm_mode == 'demo'
    assert '演示模式' in combined
    assert '完成环境配置' in combined
    assert '真实项目事项' not in combined
    assert '真实任务' not in combined
