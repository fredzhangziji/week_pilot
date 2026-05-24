"""Generate report variants from local weekly inputs."""

from __future__ import annotations

import json
import re

from weekpilot.llm import LLMProvider
from weekpilot.models import CollectedInputs, GeneratedReport
from weekpilot.prompt_builder import build_prompt_from_inputs


def generate_weekly_report_from_inputs(inputs: CollectedInputs, provider: LLMProvider) -> GeneratedReport:
    """Generate report variants directly from raw local input files."""

    prompt = build_prompt_from_inputs(inputs)
    response_text = provider.generate_text(prompt.developer_prompt, prompt.sanitized_user_prompt)
    parsed = _parse_report_json(response_text)
    warnings = list(inputs.warnings)
    if not parsed:
        warnings.append('模型输出不是预期 JSON，已将原始输出作为标准版展示。')
        parsed = {
            'standard': response_text,
            'short': _short_from_standard(response_text),
            'detailed': response_text,
            'retro': '## 个人复盘\n- 模型未返回复盘字段，建议手动补充。',
            'next_week_todo': '- [ ] 待补充下周计划',
        }
    return GeneratedReport(
        standard=parsed.get('standard', '').strip(),
        short=parsed.get('short', '').strip(),
        detailed=parsed.get('detailed', '').strip(),
        retro=parsed.get('retro', '').strip(),
        next_week_todo=parsed.get('next_week_todo', '').strip(),
        llm_mode='demo' if provider.mode == 'demo' else 'formal',
        model=provider.model,
        warnings=warnings,
    )


def render_template_reports_from_inputs(inputs: CollectedInputs, demo: bool = False) -> dict[str, str]:
    """Render deterministic demo reports directly from raw inputs."""

    prefix = '> 演示模式：以下内容由本地输入样例生成，仅用于无 API Key 时预览产品流程。\n\n' if demo else ''
    weekly_log = inputs.weekly_log.strip() or '（未提供工作日志）'
    tasks = inputs.tasks_csv.strip() or '（未提供任务表）'
    meetings = inputs.meeting_notes.strip() or '（未提供会议纪要）'

    standard = f"""{prefix}## 本周工作进展
{_markdown_block_lines(weekly_log)}

## 主要产出
- 请根据工作日志和任务表中的完成项确认主要产出。

## 风险与阻塞
- 请根据任务备注、会议纪要和工作日志中的风险描述确认阻塞项。

## 重要决策
{_markdown_block_lines(meetings)}

## 下周计划
- 请根据输入材料中的后续计划和待办事项补充。

## 需要协同/确认的问题
- 请确认输入材料中标记为待确认、缺失或依赖他人的事项。
""".strip()
    short = '演示模式：已根据样例输入生成周报草稿，请在正式模式中使用真实 API Key 生成最终版本。' if demo else '已生成周报草稿。'
    detailed = f"""{prefix}## 原始工作日志
{_markdown_block_lines(weekly_log)}

## 原始任务表
```csv
{tasks}
```

## 原始会议纪要
{_markdown_block_lines(meetings)}
""".strip()
    retro = f"""{prefix}## 个人复盘

### 收获
- 请结合本周输入材料补充具体收获。

### 问题
- 请结合风险、阻塞和未完成事项补充问题。

### 改进点
- 下周先补充更细的计划、负责人和验收口径。
""".strip()
    next_week_todo = """- [ ] 根据本周输入确认下周重点事项
- [ ] 补充待确认事项的负责人和验收口径
""".strip()
    return {
        'standard': standard,
        'short': short,
        'detailed': detailed,
        'retro': retro,
        'next_week_todo': next_week_todo,
    }


def _parse_report_json(text: str) -> dict[str, str] | None:
    stripped = text.strip()
    candidates = [stripped]
    match = re.search(r'\{.*\}', stripped, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and {'standard', 'short', 'detailed', 'retro'} <= set(data):
            keys = ['standard', 'short', 'detailed', 'retro', 'next_week_todo']
            return {key: str(data.get(key, '')) for key in keys}
    return None


def _short_from_standard(text: str) -> str:
    lines = [line.strip('-# ') for line in text.splitlines() if line.strip() and not line.startswith('```')]
    return '；'.join(lines[:4]) if lines else text[:160]


def _markdown_block_lines(text: str, max_lines: int = 12) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return '- 暂无明确记录。'
    visible = lines[:max_lines]
    rendered = []
    for line in visible:
        rendered.append(line if line.startswith(('-', '*', '#')) else f'- {line}')
    if len(lines) > max_lines:
        rendered.append(f'- 另有 {len(lines) - max_lines} 行输入未展开。')
    return '\n'.join(rendered)
