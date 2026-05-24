"""Streamlit entry point for WeekPilot."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from weekpilot.ui import adapters, layout, state
from weekpilot.ui.pages import dashboard, history, inputs, review, settings
from weekpilot.ui.styles import inject_styles

ROOT = Path(__file__).parent.resolve()
INPUT_DIR = ROOT / 'input'
OUTPUT_DIR = ROOT / 'output'
STYLE_PATH = INPUT_DIR / 'style.yaml'


def main() -> None:
    """Initialize the Streamlit app and dispatch to the selected page."""

    st.set_page_config(page_title='WeekPilot', page_icon='WP', layout='wide')
    inject_styles()
    state.init_session_state()

    style = adapters.load_settings(STYLE_PATH)
    page = layout.render_sidebar(ROOT, style)
    layout.render_top_notice(page)

    try:
        _render_page(page, style)
    except Exception as exc:  # noqa: BLE001 - top-level UI should fail with actionable context.
        st.error(f'页面渲染失败：{exc}')
        st.info('请检查本地配置、输入文件和依赖是否完整。')


def _render_page(page: str, style) -> None:
    if page == state.PAGE_DASHBOARD:
        dashboard.render(ROOT, INPUT_DIR, OUTPUT_DIR, style)
    elif page == state.PAGE_INPUTS:
        inputs.render(ROOT, INPUT_DIR, OUTPUT_DIR, style)
    elif page == state.PAGE_REVIEW:
        review.render(OUTPUT_DIR, style)
    elif page == state.PAGE_HISTORY:
        history.render(OUTPUT_DIR)
    elif page == state.PAGE_SETTINGS:
        settings.render(ROOT, STYLE_PATH, style)
    else:
        state.set_current_page(state.PAGE_DASHBOARD)
        dashboard.render(ROOT, INPUT_DIR, OUTPUT_DIR, style)


if __name__ == '__main__':
    main()
