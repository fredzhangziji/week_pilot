"""Dashboard page for the current weekly report cycle."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from weekpilot.models import ReportConfig
from weekpilot.ui import adapters, components, state


def render(root: Path, input_dir: Path, output_dir: Path, style: ReportConfig) -> None:
    """Render the Phase 1 workbench dashboard."""

    week = adapters.get_current_week_range(style)
    input_status = adapters.get_input_status(input_dir)
    model_status = adapters.get_model_status(root, style)
    privacy_status = adapters.get_privacy_status(input_dir, style)
    recent = adapters.get_recent_generation(output_dir)

    components.week_range_header(week, input_status, model_status, privacy_status)

    status_col, preview_col, result_col = st.columns([0.95, 1.45, 1.0], gap='large')
    with status_col:
        components.input_status_panel(input_status)
        components.model_status_panel(model_status)
        components.privacy_status_panel(privacy_status)

    with preview_col:
        with components.info_card('本周输入概览', '工作台只展示材料状态；输入和生成在独立页面完成。'):
            if not input_status.can_generate:
                st.info('当前还没有可用输入。补充输入材料后，这里会展示材料概览。')
            else:
                _render_input_overview(input_status, privacy_status)
                if st.button('打开输入与生成页面', use_container_width=True, key='wp_open_inputs'):
                    state.go_to(state.PAGE_INPUTS)

    with result_col:
        with components.info_card('仪表盘操作', '输入和生成已集中到独立页面。'):
            st.write('在“输入与生成”页面编辑本周材料、切换阅读模式，并执行正式或 Demo 生成。')
            if st.button('前往输入与生成', type='primary', use_container_width=True):
                state.go_to(state.PAGE_INPUTS)
        if components.recent_generation_card(recent):
            state.go_to(state.PAGE_REVIEW)


def _render_input_overview(
    input_status: adapters.InputStatusView,
    privacy_status: adapters.PrivacyStatusView,
) -> None:
    st.metric('可用输入类型', input_status.usable_file_count)
    st.metric('脱敏命中', privacy_status.detected_sensitive_count)
    rows = []
    for item in input_status.files:
        if item.name == 'style.yaml':
            continue
        rows.append(
            {
                '输入': item.label,
                '状态': '已读取' if item.has_content else ('空文件' if item.exists else '未检测到'),
                '最近修改': item.modified_at.strftime('%Y-%m-%d %H:%M') if item.modified_at else '暂无',
            }
        )
    st.table(rows)
