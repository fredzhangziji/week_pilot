"""Reusable Streamlit components for WeekPilot."""

from __future__ import annotations

from contextlib import contextmanager
from html import escape
from pathlib import Path
from typing import Iterator

import streamlit as st

from weekpilot.ui import adapters, state
from weekpilot.utils import read_text


def badge_html(label: str, tone: str = 'neutral') -> str:
    """Return a status badge HTML snippet."""

    safe_label = escape(label)
    safe_tone = tone if tone in {'success', 'warning', 'error', 'neutral'} else 'neutral'
    return f'<span class="wp-badge {safe_tone}">{safe_label}</span>'


def status_badge(label: str, tone: str = 'neutral') -> None:
    """Render one status badge."""

    st.markdown(badge_html(label, tone), unsafe_allow_html=True)


@contextmanager
def info_card(title: str, description: str = '') -> Iterator[None]:
    """Render a bordered card with a shared header."""

    with st.container(border=True):
        st.markdown(
            f"""
            <p class="wp-card-title">{escape(title)}</p>
            {f'<p class="wp-card-desc">{escape(description)}</p>' if description else ''}
            """,
            unsafe_allow_html=True,
        )
        yield


def page_header(title: str, description: str = '') -> None:
    """Render a consistent page header."""

    st.markdown(
        f"""
        <section class="wp-page-head">
          <p class="wp-page-kicker">WeekPilot</p>
          <h1 class="wp-page-title">{escape(title)}</h1>
          {f'<p class="wp-page-desc">{escape(description)}</p>' if description else ''}
        </section>
        """,
        unsafe_allow_html=True,
    )


def back_to_dashboard(key: str) -> None:
    """Render a consistent return action for secondary pages."""

    if st.button('返回本周工作台', key=key):
        state.go_to(state.PAGE_DASHBOARD)


def week_range_header(
    week: adapters.WeekRangeView,
    input_status: adapters.InputStatusView,
    model_status: adapters.ModelStatusView,
    privacy_status: adapters.PrivacyStatusView,
) -> None:
    """Render the current week and top-level readiness badges."""

    input_tone = 'success' if input_status.can_generate else 'error'
    model_tone = 'success' if model_status.api_key_configured else 'error'
    privacy_tone = 'success' if privacy_status.enabled else 'warning'
    mode_label = '正式模式可用' if input_status.can_generate and model_status.api_key_configured else '仅 Demo 可用'
    mode_tone = 'success' if input_status.can_generate and model_status.api_key_configured else 'warning'
    badges = ''.join(
        [
            badge_html(f'输入：{"已读取" if input_status.can_generate else "缺失"}', input_tone),
            badge_html(f'模型：{"可用" if model_status.api_key_configured else "未配置"}', model_tone),
            badge_html(f'隐私：{"脱敏开启" if privacy_status.enabled else "脱敏关闭"}', privacy_tone),
            badge_html(mode_label, mode_tone),
        ]
    )
    st.markdown(
        f"""
        <section class="wp-week-head">
          <div>
            <p class="wp-week-title">本周工作台</p>
            <p class="wp-week-range">{week.start.isoformat()} — {week.end.isoformat()}｜{week.week_id}</p>
          </div>
          <div class="wp-badge-row">{badges}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def input_status_panel(status: adapters.InputStatusView) -> None:
    """Render input readiness."""

    with info_card('输入文件状态', '读取本周工作日志、任务表和会议纪要。'):
        rows = []
        for file in status.files:
            if file.name == 'style.yaml':
                continue
            if file.has_content:
                value = '已读取'
            elif file.exists:
                value = '空文件'
            else:
                value = '未检测到'
            rows.append(_meta_row(file.label, value))
        rows.append(_meta_row('可用输入', f'{status.usable_file_count} 类'))
        rows.append(_meta_row('最近修改', _format_datetime(status.last_modified)))
        st.markdown(f'<div class="wp-meta-list">{"".join(rows)}</div>', unsafe_allow_html=True)
        if status.disabled_reason:
            st.warning(status.disabled_reason)


def model_status_panel(status: adapters.ModelStatusView) -> None:
    """Render model/API key readiness."""

    with info_card('模型状态', '正式生成需要有效 API Key。'):
        rows = [
            _meta_row('Provider', status.provider),
            _meta_row('Model', status.model),
            _meta_row('API Key', status.api_key_tail or '未配置'),
            _meta_row('来源', status.key_source),
            _meta_row('Base URL', status.base_url or '未配置'),
        ]
        st.markdown(f'<div class="wp-meta-list">{"".join(rows)}</div>', unsafe_allow_html=True)
        if status.disabled_reason:
            st.warning(status.disabled_reason)


def privacy_status_panel(status: adapters.PrivacyStatusView) -> None:
    """Render privacy masking readiness."""

    with info_card('隐私脱敏', '正式发送给模型前使用本地脱敏设置。'):
        rows = [
            _meta_row('状态', '已开启' if status.enabled else '已关闭'),
            _meta_row('命中数量', str(status.detected_sensitive_count)),
            _meta_row('规则类型', '、'.join(status.sensitive_types) if status.sensitive_types else '未启用具体规则'),
        ]
        st.markdown(f'<div class="wp-meta-list">{"".join(rows)}</div>', unsafe_allow_html=True)
        if not status.enabled:
            st.warning('脱敏已关闭。正式生成前请确认输入材料可发送给模型。')
        for issue in status.blocking_issues:
            st.error(issue)


def generation_panel(can_generate_official: bool, official_disabled_reason: str | None) -> tuple[bool, bool]:
    """Render formal/demo generation controls and return clicked states."""

    with info_card('生成周报', '正式模式读取真实输入；Demo 模式只使用通用样例数据。'):
        st.markdown(
            """
            <div class="wp-safe-note">
            Demo 模式仅用于体验流程，不读取你的真实工作日志、任务表或会议纪要，生成结果会明确标记为演示内容。
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write('')
        formal_clicked = st.button(
            '生成正式周报',
            type='primary',
            disabled=not can_generate_official,
            use_container_width=True,
            key='wp_generate_formal',
        )
        demo_clicked = st.button('使用 Demo 数据体验', use_container_width=True, key='wp_generate_demo')
        if official_disabled_reason:
            st.caption(official_disabled_reason)
        return formal_clicked, demo_clicked


def recent_generation_card(recent: adapters.RecentGenerationView) -> bool:
    """Render latest generation metadata and return whether open was clicked."""

    with info_card('最近一次生成', '生成后可进入审阅页继续处理。'):
        if not recent.exists:
            st.markdown('<p class="wp-empty">本周还没有生成过周报。</p>', unsafe_allow_html=True)
            return False
        rows = [
            _meta_row('周期', _week_range_text(recent.week_start, recent.week_end, recent.week_id)),
            _meta_row('生成时间', _format_datetime(recent.generated_at)),
            _meta_row('模式', recent.mode or '未知'),
            _meta_row('模型', recent.model or '未知'),
            _meta_row('质量检查', recent.quality_status or '未检查'),
            _meta_row('保存状态', '已保存' if recent.saved else '已写入输出目录'),
        ]
        st.markdown(f'<div class="wp-meta-list">{"".join(rows)}</div>', unsafe_allow_html=True)
        return st.button('查看审阅页', use_container_width=True, key='wp_open_recent_generation')


def report_tabs(root: Path, read_only: bool = True) -> None:
    """Render report artifact tabs from an output/history directory."""

    labels = ['标准周报', '简洁版', '详细版', '个人复盘', '下周 TODO', '质量检查']
    files = [
        'weekly_report.md',
        'weekly_report_short.md',
        'weekly_report_detailed.md',
        'weekly_retro.md',
        'next_week_todo.md',
        'report_quality.md',
    ]
    tabs = st.tabs(labels)
    for tab, filename in zip(tabs, files):
        with tab:
            content = read_text(root / filename)
            if not content.strip():
                st.info('暂无内容。')
                continue
            if read_only:
                st.markdown(content)
            else:
                st.text_area(filename, value=content, height=420, label_visibility='collapsed')
            st.download_button(
                '下载 Markdown',
                content,
                file_name=filename,
                mime='text/markdown',
                key=f'wp_download_{root}_{filename}',
            )


@contextmanager
def settings_section(title: str, description: str = '') -> Iterator[None]:
    """Render one settings section."""

    with info_card(title, description):
        yield


def _meta_row(label: str, value: str) -> str:
    return f'<div class="wp-meta-row"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'


def _format_datetime(value) -> str:
    if value is None:
        return '暂无'
    return value.strftime('%Y-%m-%d %H:%M')


def _week_range_text(start: str, end: str, fallback: str) -> str:
    if start and end:
        return f'{start} — {end}'
    return fallback or '未知'
