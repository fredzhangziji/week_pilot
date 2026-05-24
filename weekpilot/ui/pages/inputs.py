"""Input editing, reading, and report generation page."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

from weekpilot.llm import MissingAPIKeyError
from weekpilot.models import ReportConfig
from weekpilot.ui import adapters, components, state
from weekpilot.utils import read_text, write_text

INPUT_FILES = {
    'weekly_log.md': {
        'label': 'weekly_log',
        'description': '记录本周完成事项、进行中事项、问题和下周计划。',
        'height': 360,
        'template': '# Weekly Log\n\n- 周一：\n- 周二：\n- 周三：\n- 周四：\n- 周五：\n',
    },
    'tasks.csv': {
        'label': 'tasks',
        'description': '任务表字段：task,status,priority,due_date,note。',
        'height': 300,
        'template': 'task,status,priority,due_date,note\n',
    },
    'meeting_notes.md': {
        'label': 'meeting_notes',
        'description': '记录会议结论、重要决策、风险和后续动作。',
        'height': 320,
        'template': '# Meeting Notes\n\n- \n',
    },
}

FILE_SELECT_KEY = 'wp_input_file'
MODE_KEY = 'wp_input_mode'
LAST_AUTOSAVE_KEY = 'wp_last_autosave'


def render(root: Path, input_dir: Path, output_dir: Path, style: ReportConfig) -> None:
    """Render input editor, read preview, model-input preview, and generation controls."""

    components.page_header('输入与生成', '编辑本周输入材料，切换阅读预览，并在同一页面生成周报。')
    components.back_to_dashboard('wp_inputs_back_top')

    input_status = adapters.get_input_status(input_dir)
    model_status = adapters.get_model_status(root, style)
    privacy_status = adapters.get_privacy_status(input_dir, style)

    left_col, right_col = st.columns([1.45, 1], gap='large')
    with left_col:
        _render_file_workspace(input_dir)
    with right_col:
        components.input_status_panel(input_status)
        components.model_status_panel(model_status)
        components.privacy_status_panel(privacy_status)

    preview_col, generation_col = st.columns([1.4, 1], gap='large')
    with preview_col:
        _render_model_input_preview(input_dir, style, input_status)
    with generation_col:
        _render_generation(root, input_dir, output_dir, input_status, model_status)


def _render_file_workspace(input_dir: Path) -> None:
    with components.info_card('输入工作区', '切换文件后可输入或阅读预览；输入内容会自动保存到本地文件。'):
        selected_file = st.selectbox(
            '输入文件',
            list(INPUT_FILES),
            format_func=lambda filename: INPUT_FILES[filename]['label'],
            key=FILE_SELECT_KEY,
        )
        mode = st.radio(
            '工作模式',
            ['输入模式', '阅读模式'],
            horizontal=True,
            key=MODE_KEY,
        )
        file_path = input_dir / selected_file
        meta = INPUT_FILES[selected_file]
        st.caption(f"{meta['description']} 保存位置：{file_path}")

        if mode == '输入模式':
            _render_input_mode(file_path, selected_file, meta)
        else:
            _render_read_mode(file_path, selected_file)


def _render_input_mode(file_path: Path, selected_file: str, meta: dict[str, object]) -> None:
    editor_key = _editor_key(selected_file)
    seed_key = f'{editor_key}_seed'
    _load_editor_from_file(file_path, editor_key, seed_key)

    if not st.session_state.get(editor_key) and st.button('插入基础模板', key=f'wp_template_{selected_file}'):
        st.session_state[editor_key] = str(meta['template'])
        _autosave(file_path, editor_key)

    st.text_area(
        '文件内容',
        key=editor_key,
        height=int(meta['height']),
        label_visibility='collapsed',
        on_change=_autosave,
        args=(file_path, editor_key),
    )
    saved_at = st.session_state.get(LAST_AUTOSAVE_KEY)
    st.caption(saved_at or '输入后会自动保存。')


def _render_read_mode(file_path: Path, selected_file: str) -> None:
    content = read_text(file_path)
    if not content.strip():
        st.info('当前文件为空。切换到输入模式补充内容。')
        return
    if selected_file.endswith('.csv'):
        try:
            frame = pd.read_csv(StringIO(content))
        except Exception:  # noqa: BLE001 - bad CSV should still be readable as text.
            st.code(content, language='text')
        else:
            st.dataframe(frame, use_container_width=True)
        return
    st.markdown(content)


def _render_model_input_preview(input_dir: Path, style: ReportConfig, input_status: adapters.InputStatusView) -> None:
    with components.info_card('发送给模型的输入预览', '正式生成会把原始输入脱敏后直接交给 LLM，不再做规则抽取。'):
        if not input_status.can_generate:
            st.info('当前没有可用输入材料。')
            return
        preview = adapters.get_sanitized_input_preview(input_dir, style)
        st.caption(
            f'脱敏命中 {preview.replacement_count} 处'
            f'{"，类型：" + "、".join(preview.replacement_labels) if preview.replacement_labels else ""}'
        )
        tabs = st.tabs(['weekly_log', 'tasks', 'meeting_notes'])
        with tabs[0]:
            _render_preview_text(preview.weekly_log, 'markdown')
        with tabs[1]:
            _render_preview_text(preview.tasks_csv, 'csv')
        with tabs[2]:
            _render_preview_text(preview.meeting_notes, 'markdown')


def _render_preview_text(content: str, language: str) -> None:
    if not content.strip():
        st.info('未提供内容。')
    elif language == 'markdown':
        st.markdown(content)
    else:
        st.code(content, language=language)


def _render_generation(
    root: Path,
    input_dir: Path,
    output_dir: Path,
    input_status: adapters.InputStatusView,
    model_status: adapters.ModelStatusView,
) -> None:
    official_disabled_reason = _official_disabled_reason(input_status, model_status)
    formal_clicked, demo_clicked = components.generation_panel(
        can_generate_official=official_disabled_reason is None,
        official_disabled_reason=official_disabled_reason,
    )
    if formal_clicked:
        _run_generation(root, input_dir, output_dir, demo=False)
    if demo_clicked:
        _run_generation(root, input_dir, output_dir, demo=True)


def _official_disabled_reason(
    input_status: adapters.InputStatusView,
    model_status: adapters.ModelStatusView,
) -> str | None:
    if not input_status.can_generate:
        return input_status.disabled_reason
    if not model_status.official_generation_available:
        return model_status.disabled_reason
    return None


def _run_generation(root: Path, input_dir: Path, output_dir: Path, demo: bool) -> None:
    mode_label = 'Demo' if demo else '正式'
    try:
        with st.spinner(f'正在生成{mode_label}周报...'):
            result = adapters.generate_report(root=root, input_dir=input_dir, output_dir=output_dir, demo=demo)
    except MissingAPIKeyError as exc:
        st.error(str(exc))
        return
    except RuntimeError as exc:
        st.error(str(exc))
        st.info('请检查 Provider、模型、Base URL 和 API Key 是否匹配。')
        return
    state.save_generation_result(result)
    state.go_to(state.PAGE_REVIEW)


def _autosave(file_path: Path, editor_key: str) -> None:
    content = st.session_state.get(editor_key, '')
    write_text(file_path, content)
    st.session_state[LAST_AUTOSAVE_KEY] = f'已自动保存到 {file_path.name}'


def _load_editor_from_file(file_path: Path, editor_key: str, seed_key: str) -> None:
    path_key = str(file_path)
    if st.session_state.get(seed_key) == path_key and editor_key in st.session_state:
        return
    st.session_state[editor_key] = read_text(file_path)
    st.session_state[seed_key] = path_key


def _editor_key(filename: str) -> str:
    return f'wp_editor_{filename.replace(".", "_")}'
