"""Global layout helpers for the Streamlit app."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from weekpilot.models import ReportConfig
from weekpilot.ui import adapters, state


def render_sidebar(root: str | Path, style: ReportConfig) -> str:
    """Render the primary navigation and return the selected page."""

    model_status = adapters.get_model_status(root, style)
    with st.sidebar:
        st.markdown(
            """
            <div class="wp-brand">
              <p class="wp-brand-title">WeekPilot</p>
              <p class="wp-brand-caption">本地周报工作台</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected = st.radio(
            '页面导航',
            list(state.PAGE_LABELS),
            index=list(state.PAGE_LABELS).index(state.current_page()),
            format_func=lambda page: state.PAGE_LABELS[page],
            key=state.NAV_PAGE_KEY,
        )
        if selected != state.current_page():
            state.set_current_page(selected)

        st.divider()
        if model_status.api_key_configured:
            st.caption(f'正式模式：{model_status.provider} / {model_status.model}')
        else:
            st.caption('正式模式：未配置 API Key')
            st.caption('Demo 模式可用于体验流程。')
    return state.current_page()


def render_top_notice(page: str) -> None:
    """Render a compact page-level description."""

    description = state.PAGE_DESCRIPTIONS.get(page, '')
    if description:
        st.caption(description)
