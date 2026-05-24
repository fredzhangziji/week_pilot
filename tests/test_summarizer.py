"""Summarizer tests."""

from weekpilot.collector import collect_inputs
from weekpilot.llm import DemoLLMProvider
from weekpilot.sample_data import write_sample_inputs
from weekpilot.summarizer import generate_weekly_report_from_inputs


def test_summarizer_generates_required_weekly_sections(tmp_path):
    input_dir = tmp_path / 'input'
    write_sample_inputs(input_dir)
    collected = collect_inputs(input_dir)

    report = generate_weekly_report_from_inputs(collected, DemoLLMProvider(collected))

    assert '## 本周工作进展' in report.standard
    assert '## 风险与阻塞' in report.standard
    assert '## 下周计划' in report.standard
    assert report.llm_mode == 'demo'
