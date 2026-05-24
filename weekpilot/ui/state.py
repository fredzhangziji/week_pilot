"""Session state helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

PAGE_DASHBOARD = 'dashboard'
PAGE_INPUTS = 'inputs'
PAGE_REVIEW = 'review'
PAGE_HISTORY = 'history'
PAGE_SETTINGS = 'settings'

PAGE_LABELS = {
    PAGE_DASHBOARD: '本周工作台',
    PAGE_INPUTS: '输入与生成',
    PAGE_REVIEW: '周报审阅',
    PAGE_HISTORY: '历史周报',
    PAGE_SETTINGS: '设置',
}

PAGE_DESCRIPTIONS = {
    PAGE_DASHBOARD: '查看本周周报状态、材料质量和最近生成结果。',
    PAGE_INPUTS: '编辑输入文件、阅读预览、查看摘要并生成周报。',
    PAGE_REVIEW: '审阅、复制、下载和保存生成结果。',
    PAGE_HISTORY: '按周回看历史周报和下周待办。',
    PAGE_SETTINGS: '维护模型、周期、风格和隐私设置。',
}

CURRENT_PAGE_KEY = 'wp_current_page'
NAV_PAGE_KEY = 'wp_nav_page'
PENDING_PAGE_KEY = 'wp_pending_page'
LAST_GENERATION_KEY = 'wp_last_generation'
MODEL_TEST_RESULT_KEY = 'wp_model_test_result'


def init_session_state() -> None:
    """Initialize UI session keys once per Streamlit session."""

    pending_page = st.session_state.pop(PENDING_PAGE_KEY, None)
    current = st.session_state.get(CURRENT_PAGE_KEY)
    nav_page = st.session_state.get(NAV_PAGE_KEY)
    if pending_page in PAGE_LABELS:
        page = pending_page
    elif nav_page in PAGE_LABELS and nav_page != current:
        page = nav_page
    elif current in PAGE_LABELS:
        page = current
    elif nav_page in PAGE_LABELS:
        page = nav_page
    else:
        page = PAGE_DASHBOARD
    if page not in PAGE_LABELS:
        page = PAGE_DASHBOARD
    st.session_state[CURRENT_PAGE_KEY] = page
    st.session_state[NAV_PAGE_KEY] = page
    st.session_state.setdefault(LAST_GENERATION_KEY, None)
    st.session_state.setdefault(MODEL_TEST_RESULT_KEY, None)


def current_page() -> str:
    """Return the current page id."""

    page = st.session_state.get(CURRENT_PAGE_KEY, PAGE_DASHBOARD)
    return page if page in PAGE_LABELS else PAGE_DASHBOARD


def set_current_page(page: str) -> None:
    """Set the active page without forcing a rerun."""

    if page not in PAGE_LABELS:
        page = PAGE_DASHBOARD
    st.session_state[CURRENT_PAGE_KEY] = page


def go_to(page: str) -> None:
    """Navigate to a page and rerun Streamlit."""

    if page not in PAGE_LABELS:
        page = PAGE_DASHBOARD
    st.session_state[PENDING_PAGE_KEY] = page
    st.session_state[CURRENT_PAGE_KEY] = page
    st.rerun()


def save_generation_result(result: Any) -> None:
    """Store the latest generation result for this UI session."""

    st.session_state[LAST_GENERATION_KEY] = result


def latest_generation_result() -> Any:
    """Return the latest generation result, if any."""

    return st.session_state.get(LAST_GENERATION_KEY)
