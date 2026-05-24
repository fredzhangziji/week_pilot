"""Weekly report history page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from weekpilot.ui import adapters, components, state


def render(output_dir: Path) -> None:
    """Render history entries by week instead of raw files."""

    components.page_header('历史周报', '按周回看已生成周报，避免把历史页做成文件列表。')
    components.back_to_dashboard('wp_history_back_top')
    items = adapters.get_history_items(output_dir)
    if not items:
        st.info('还没有保存过周报。请先从本周工作台生成一次周报。')
        if st.button('返回本周工作台', type='primary', key='wp_history_back_empty'):
            state.go_to(state.PAGE_DASHBOARD)
        return

    selected_label = st.selectbox(
        '选择周报',
        [item.week_id for item in items],
        format_func=lambda week_id: _history_label(next(item for item in items if item.week_id == week_id)),
    )
    selected = next(item for item in items if item.week_id == selected_label)

    with components.info_card('历史元信息', '历史按周组织，文件名仅作为底层存储细节。'):
        st.table(
            [
                {'项目': '周期', '状态': _week_range(selected)},
                {
                    '项目': '生成时间',
                    '状态': selected.generated_at.strftime('%Y-%m-%d %H:%M') if selected.generated_at else '暂无',
                },
                {'项目': '模式', '状态': selected.mode or '未知'},
                {'项目': '模型', '状态': selected.model or '未知'},
                {'项目': '质量检查', '状态': selected.quality_status or '未检查'},
                {'项目': '下周 TODO 候选', '状态': str(selected.todo_count)},
            ]
        )

    components.report_tabs(selected.path, read_only=True)


def _history_label(item: adapters.HistoryItemView) -> str:
    range_text = _week_range(item)
    mode = item.mode or '未知模式'
    quality = item.quality_status or '未检查'
    return f'{item.week_id}｜{range_text}｜{mode}｜{quality}'


def _week_range(item: adapters.HistoryItemView) -> str:
    if item.week_start and item.week_end:
        return f'{item.week_start} — {item.week_end}'
    return item.week_id
