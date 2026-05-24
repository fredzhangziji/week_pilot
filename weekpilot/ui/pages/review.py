"""Report review page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from weekpilot.models import ReportConfig
from weekpilot.ui import adapters, components, state


def render(output_dir: Path, style: ReportConfig) -> None:
    """Render generated report artifacts for review."""

    components.page_header('周报审阅', '生成后在这里审阅不同版本、下载 Markdown，并继续保存历史。')
    components.back_to_dashboard('wp_review_back_top')
    recent = adapters.get_recent_generation(output_dir)
    if not recent.exists:
        st.info('本周还没有生成结果。请先从本周工作台生成周报。')
        if st.button('返回本周工作台', type='primary', key='wp_review_back_empty'):
            state.go_to(state.PAGE_DASHBOARD)
        return

    week = adapters.get_current_week_range(style)
    with components.info_card('生成元信息', 'Phase 1 使用已有输出文件；Phase 2 会加入编辑和保存状态。'):
        rows = {
            '周期': f'{recent.week_start or week.start} — {recent.week_end or week.end}',
            '生成时间': recent.generated_at.strftime('%Y-%m-%d %H:%M') if recent.generated_at else '暂无',
            '模式': recent.mode or '未知',
            '模型': recent.model or '未知',
            '质量检查': recent.quality_status or '未检查',
            '保存状态': '已保存' if recent.saved else '已写入输出目录',
        }
        st.table([{'项目': key, '状态': value} for key, value in rows.items()])

    components.report_tabs(output_dir, read_only=False)
