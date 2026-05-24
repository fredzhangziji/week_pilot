"""End-to-end generation pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path

from weekpilot.collector import collect_inputs
from weekpilot.critic import evaluate_report
from weekpilot.exporter import export_outputs
from weekpilot.history import apply_week_metadata, save_history
from weekpilot.llm import DemoLLMProvider, LLMProvider, provider_from_config
from weekpilot.models import PipelineResult
from weekpilot.sample_data import write_sample_inputs


def run_generate(
    input_dir: str | Path,
    output_dir: str | Path,
    project_root: str | Path | None = None,
    demo: bool = False,
    provider: LLMProvider | None = None,
) -> PipelineResult:
    """Run collection, privacy-aware generation, critic, export, and history save."""

    root = Path(project_root or Path.cwd())
    collected = _collect_inputs_for_mode(input_dir, demo)
    selected_provider = provider
    if selected_provider is None:
        selected_provider = (
            DemoLLMProvider(inputs=collected)
            if demo
            else provider_from_config(str(root), collected.style)
        )
    elif isinstance(selected_provider, DemoLLMProvider):
        selected_provider.inputs = collected

    from weekpilot.summarizer import generate_weekly_report_from_inputs

    report = generate_weekly_report_from_inputs(collected, selected_provider)
    report = apply_week_metadata(report, collected.style)
    if not report.next_week_todo:
        report.next_week_todo = '- [ ] 待补充下周计划\n'
    report.quality_report = evaluate_report(report, collected.style)
    export_outputs(collected, report, output_dir)
    history_dir = save_history(output_dir, report)
    return PipelineResult(
        inputs=collected,
        report=report,
        output_dir=str(output_dir),
        history_dir=str(history_dir),
        file_statuses=collected.file_statuses,
    )


def _collect_inputs_for_mode(input_dir: str | Path, demo: bool):
    if not demo:
        return collect_inputs(input_dir)
    with tempfile.TemporaryDirectory(prefix='weekpilot_demo_') as demo_dir:
        write_sample_inputs(demo_dir)
        return collect_inputs(demo_dir)
