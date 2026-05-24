"""Quality checks for generated reports."""

from __future__ import annotations

from weekpilot.models import GeneratedReport, ReportConfig

OVERCLAIM_WORDS = ('显著', '重大突破', '全面完成', '完全解决', '大幅提升')


def evaluate_report(report: GeneratedReport, config: ReportConfig) -> str:
    """Return a markdown quality report."""

    score = 100
    high: list[str] = []
    medium: list[str] = []
    low: list[str] = []
    text = '\n'.join([report.standard, report.short, report.detailed, report.retro])

    if not _has_heading(report.standard, '本周工作进展'):
        score -= 12
        high.append('标准版缺少“本周工作进展”章节。')
    if not _has_heading(report.standard, '主要产出'):
        score -= 10
        medium.append('标准版缺少“主要产出”章节，容易变成流水账。')
    if not _has_heading(report.standard, '风险与阻塞'):
        score -= 8
        medium.append('标准版缺少“风险与阻塞”章节。')
    if not _has_heading(report.standard, '下周计划'):
        score -= 12
        high.append('标准版缺少“下周计划”章节。')

    for word in OVERCLAIM_WORDS:
        if word in text:
            score -= 6
            medium.append(f'报告中出现可能夸大的表达：“{word}”。')

    sensitive_terms = [term for term in [*config.privacy.forbidden_terms, *config.privacy.custom_sensitive_terms] if term]
    leaked_terms = [term for term in sensitive_terms if term in text]
    if leaked_terms:
        score -= min(20, 5 * len(leaked_terms))
        high.append('报告中仍出现配置的敏感词，建议检查脱敏设置。')

    if _looks_like_changelog_only(report.standard):
        score -= 8
        low.append('报告可能偏流水账，建议补充产出、风险和下周动作。')
    if '暂无' in report.standard:
        low.append('报告包含“暂无”类占位表达，建议人工确认是否准确。')

    score = max(score, 0)
    return _render_quality(score, high, medium, low)


def _has_heading(text: str, heading: str) -> bool:
    return f'## {heading}' in text or f'### {heading}' in text


def _looks_like_changelog_only(text: str) -> bool:
    headings = [line for line in text.splitlines() if line.startswith('## ')]
    bullets = [line for line in text.splitlines() if line.strip().startswith('- ')]
    return len(bullets) > 8 and len(headings) < 3


def _render_quality(score: int, high: list[str], medium: list[str], low: list[str]) -> str:
    def section(items: list[str], empty: str) -> str:
        return '\n'.join(f'- {item}' for item in items) if items else f'- {empty}'

    return f"""## 质量评分
总分：{score} / 100

## 问题清单

### 高优问题
{section(high, '暂无高优问题。')}

### 中优问题
{section(medium, '暂无中优问题。')}

### 低优问题
{section(low, '暂无低优问题。')}

## 修改建议
- 优先确认风险、阻塞和下周计划是否完整。
- 对“待确认”的事项补充明确动作和协作对象。
- 发送前快速检查语气是否自然，避免夸大事实。
"""
