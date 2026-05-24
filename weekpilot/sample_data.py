"""Sample input generation."""

from __future__ import annotations

from pathlib import Path

from weekpilot.config import DEFAULT_STYLE
from weekpilot.utils import ensure_dir, write_text

WEEKLY_LOG = """# Weekly Log

- 周一：阅读示例项目背景，完成本地环境配置。
- 周二：梳理研发任务需求和上下游依赖，补充流程文档。
- 周三：完成方案草稿，发现测试标准不清晰，需要协作方进一步确认。
- 周四：开发 demo 脚本，遇到测试数据缺失，当前先完成主流程验证。
- 周五：整理本周进展，准备下周计划。
"""

TASKS_CSV = """task,status,priority,due_date,note
完成环境配置,done,P1,2026-05-11,
梳理流程文档,done,P1,2026-05-12,
完成 demo 脚本,in_progress,P0,2026-05-16,缺少测试数据样例
补充测试用例,todo,P1,2026-05-20,
确认验收标准,blocked,P0,2026-05-20,需要协作方确认
"""

MEETING_NOTES = """# Meeting Notes

- 本周确认了核心流程优先级。
- 当前版本先覆盖主流程。
- 异常场景后续迭代。
- 测试标准需要进一步确认。
"""

STYLE_YAML = """report_type: weekly
language: zh-CN
audience: manager
style: concise_professional
length: medium
week_start_day: 0
week_end_day: 4
focus:
  - progress
  - deliverables
  - risks
  - next_week_plan
output_versions:
  - standard
  - short
  - detailed
  - retro
privacy:
  enabled: true
  preview_before_send: true
  masking_strategy: role_preserving
  forbidden_terms: []
  custom_sensitive_terms: []
  mask_emails: true
  mask_phone_numbers: true
  mask_urls: true
  mask_amounts: true
llm:
  provider: openai
  model: gpt-5.1-mini
  base_url: https://api.openai.com/v1
  active_key_name:
"""


def write_sample_inputs(input_dir: str | Path) -> list[Path]:
    """Create sample input files."""

    root = ensure_dir(input_dir)
    files = {
        'weekly_log.md': WEEKLY_LOG,
        'tasks.csv': TASKS_CSV,
        'meeting_notes.md': MEETING_NOTES,
        'style.yaml': STYLE_YAML,
    }
    return [write_text(root / filename, content) for filename, content in files.items()]


def default_style_yaml() -> str:
    """Return the canonical sample style YAML."""

    import yaml

    return yaml.safe_dump(DEFAULT_STYLE, allow_unicode=True, sort_keys=False)
