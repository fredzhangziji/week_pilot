"""Settings page for model, week, report, and privacy configuration."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from weekpilot.config import active_api_key, load_api_key_store, save_api_key_store, upsert_api_key
from weekpilot.models import ApiKeyEntry, ApiKeyStore, ReportConfig
from weekpilot.ui import adapters, components, state

PROVIDER_DEFAULTS = {
    'openai': {'model': 'gpt-5.1-mini', 'base_url': 'https://api.openai.com/v1'},
    'deepseek': {'model': 'deepseek-v4-flash', 'base_url': 'https://api.deepseek.com'},
    'openai-compatible': {'model': 'custom-model', 'base_url': 'http://localhost:8000/v1'},
}

WEEKDAYS = {
    0: '周一',
    1: '周二',
    2: '周三',
    3: '周四',
    4: '周五',
    5: '周六',
    6: '周日',
}


def render(root: Path, style_path: Path, style: ReportConfig) -> None:
    """Render settings sections."""

    components.page_header('设置', '集中维护模型、周期、报告风格、隐私脱敏和 Demo 模式说明。')
    components.back_to_dashboard('wp_settings_back_top')
    _render_api_settings(root, style_path, style)
    _render_week_and_privacy_settings(style_path, style)
    _render_report_style_settings(style_path, style)
    _render_demo_mode_section()


def _render_api_settings(root: Path, style_path: Path, style: ReportConfig) -> None:
    store = load_api_key_store(root)
    active_key = active_api_key(root, style)
    model_status = adapters.get_model_status(root, style)

    with components.settings_section('API Key 与模型', 'API Key 仅用于本地调用模型，不会写死在代码中。'):
        if model_status.api_key_configured:
            st.success(f'当前可用于正式生成：{model_status.provider} / {model_status.model}')
            st.caption(f'Key：{model_status.api_key_tail}｜来源：{model_status.key_source}')
        else:
            st.warning('未配置 API Key。正式生成不可用，Demo 模式仍可体验流程。')
        st.caption('请不要将包含 API Key 的本地配置文件提交到 Git。UI 不会长期明文展示完整 Key。')

        if st.button('本地校验模型配置', use_container_width=True):
            st.session_state[state.MODEL_TEST_RESULT_KEY] = adapters.test_model_connection(root, style)
        test_result = st.session_state.get(state.MODEL_TEST_RESULT_KEY)
        if test_result:
            (st.success if test_result.ok else st.error)(test_result.message)

        if store.keys:
            options = [key.name for key in store.keys]
            default_index = _default_key_index(options, active_key)
            selected_name = st.selectbox('已有本地配置', options, index=default_index)
            selected_key = next(key for key in store.keys if key.name == selected_name)
            if st.button('激活所选配置', disabled=selected_key.is_active, use_container_width=True):
                _activate_key(root, style_path, style, store, selected_key.name)
                st.success(f'已激活 {selected_key.name}。')
                st.rerun()

        with st.form('wp_api_key_form'):
            st.markdown('**新增或更新本地配置**')
            entry_options = ['新建配置'] + [key.name for key in store.keys]
            selected_entry = st.selectbox('编辑对象', entry_options)
            existing_entry = (
                None
                if selected_entry == '新建配置'
                else next(key for key in store.keys if key.name == selected_entry)
            )

            current_provider = _provider_for(style, existing_entry or active_key)
            provider = st.selectbox(
                'Provider',
                list(PROVIDER_DEFAULTS),
                index=list(PROVIDER_DEFAULTS).index(current_provider),
            )
            defaults = PROVIDER_DEFAULTS[provider]
            name = st.text_input('名称', value=existing_entry.name if existing_entry else 'default')
            model = st.text_input('Model', value=_model_for(provider, style, existing_entry or active_key))
            base_url = st.text_input('Base URL', value=_base_url_for(provider, style, existing_entry or active_key))
            api_key = st.text_input('API Key', type='password', help='更新已有配置时，留空会保留原 Key。')

            submitted = st.form_submit_button('保存并激活')
            if submitted:
                key_name = name.strip()
                old_key = next((key for key in store.keys if key.name == key_name), existing_entry)
                clean_key = api_key.strip() or (old_key.api_key if old_key else '')
                if not key_name:
                    st.error('名称不能为空。')
                elif not clean_key:
                    st.error('API Key 不能为空。')
                else:
                    clean_model = model.strip() or defaults['model']
                    clean_base_url = base_url.strip() or defaults['base_url']
                    upsert_api_key(
                        root,
                        ApiKeyEntry(
                            name=key_name,
                            provider=provider,
                            api_key=clean_key,
                            model=clean_model,
                            base_url=clean_base_url,
                            is_active=True,
                        ),
                    )
                    _save_llm_style(style_path, style, provider, clean_model, clean_base_url, key_name)
                    st.success('已保存并激活。')
                    st.rerun()

        if store.keys and st.button('清除所有本地 API Key 配置', use_container_width=True):
            save_api_key_store(root, ApiKeyStore())
            _save_llm_style(style_path, style, style.llm.provider, style.llm.model, style.llm.base_url, '')
            st.success('已清除本地 API Key 配置。环境变量不受影响。')
            st.rerun()


def _render_week_and_privacy_settings(style_path: Path, style: ReportConfig) -> None:
    with components.settings_section('周期与隐私', '首页和生成流程会读取这里的周期和脱敏设置。'):
        with st.form('wp_week_privacy_form'):
            col_start, col_end = st.columns(2)
            week_start_day = col_start.selectbox(
                '本周开始日',
                list(WEEKDAYS),
                index=list(WEEKDAYS).index(style.week_start_day),
                format_func=WEEKDAYS.get,
            )
            week_end_day = col_end.selectbox(
                '本周结束日',
                list(WEEKDAYS),
                index=list(WEEKDAYS).index(style.week_end_day),
                format_func=WEEKDAYS.get,
            )
            preview_style = style.model_copy(update={'week_start_day': week_start_day, 'week_end_day': week_end_day})
            preview_week = adapters.get_current_week_range(preview_style)
            st.caption(f'当前设置下，本周为 {preview_week.week_id}：{preview_week.start} 至 {preview_week.end}')

            privacy_enabled = st.checkbox('发送给模型前进行本地脱敏', value=style.privacy.enabled)
            preview_before_send = st.checkbox('生成前展示脱敏摘要', value=style.privacy.preview_before_send)
            mask_cols = st.columns(4)
            mask_emails = mask_cols[0].checkbox('邮箱', value=style.privacy.mask_emails)
            mask_phone_numbers = mask_cols[1].checkbox('联系方式', value=style.privacy.mask_phone_numbers)
            mask_urls = mask_cols[2].checkbox('链接', value=style.privacy.mask_urls)
            mask_amounts = mask_cols[3].checkbox('金额', value=style.privacy.mask_amounts)
            custom_terms = st.text_area(
                '自定义脱敏词表（每行一个）',
                value='\n'.join(style.privacy.custom_sensitive_terms),
            )

            submitted = st.form_submit_button('保存周期与隐私设置')
            if submitted:
                updated = style.model_copy(
                    update={
                        'week_start_day': week_start_day,
                        'week_end_day': week_end_day,
                        'privacy': style.privacy.model_copy(
                            update={
                                'enabled': privacy_enabled,
                                'preview_before_send': preview_before_send,
                                'mask_emails': mask_emails,
                                'mask_phone_numbers': mask_phone_numbers,
                                'mask_urls': mask_urls,
                                'mask_amounts': mask_amounts,
                                'custom_sensitive_terms': [
                                    line.strip() for line in custom_terms.splitlines() if line.strip()
                                ],
                            }
                        ),
                    }
                )
                adapters.save_settings(updated, style_path)
                st.success('周期与隐私设置已保存。')
                st.rerun()


def _render_report_style_settings(style_path: Path, style: ReportConfig) -> None:
    with components.settings_section('报告风格', 'MVP 阶段保持少量可控选项，避免模板过度复杂。'):
        with st.form('wp_report_style_form'):
            audience = st.selectbox(
                '受众',
                ['manager', 'team', 'self'],
                index=['manager', 'team', 'self'].index(style.audience),
            )
            tone = st.selectbox(
                '风格',
                ['concise_professional', 'detailed_professional', 'retro'],
                index=['concise_professional', 'detailed_professional', 'retro'].index(style.style),
            )
            length = st.selectbox(
                '长度',
                ['short', 'medium', 'long'],
                index=['short', 'medium', 'long'].index(style.length),
            )
            focus = st.multiselect(
                '关注重点',
                ['progress', 'deliverables', 'risks', 'next_week_plan', 'decisions', 'retro'],
                default=style.focus,
            )
            if st.form_submit_button('保存报告风格'):
                updated = style.model_copy(
                    update={'audience': audience, 'style': tone, 'length': length, 'focus': focus}
                )
                adapters.save_settings(updated, style_path)
                st.success('报告风格已保存。')
                st.rerun()


def _render_demo_mode_section() -> None:
    with components.settings_section('Demo 模式说明', 'Demo 模式只用于体验产品流程。'):
        st.markdown(
            """
            Demo 模式使用通用职场样例数据，不会读取你的真实工作日志、任务表或会议纪要。
            Demo 结果会明确标记为演示内容，不应作为正式周报提交。
            """
        )


def _activate_key(root: Path, style_path: Path, style: ReportConfig, store: ApiKeyStore, selected_name: str) -> None:
    activated = None
    updated_keys = []
    for key in store.keys:
        is_active = key.name == selected_name
        updated = key.model_copy(update={'is_active': is_active})
        updated_keys.append(updated)
        if is_active:
            activated = updated
    save_api_key_store(root, ApiKeyStore(keys=updated_keys))
    if activated:
        _save_llm_style(style_path, style, activated.provider, activated.model, activated.base_url, activated.name)


def _save_llm_style(
    style_path: Path,
    style: ReportConfig,
    provider: str,
    model: str,
    base_url: str,
    key_name: str | None,
) -> None:
    updated = style.model_copy(
        update={
            'llm': style.llm.model_copy(
                update={
                    'provider': provider,
                    'model': model,
                    'base_url': base_url,
                    'active_key_name': key_name or None,
                }
            )
        }
    )
    adapters.save_settings(updated, style_path)


def _default_key_index(options: list[str], active_key: ApiKeyEntry | None) -> int:
    if active_key and active_key.name in options:
        return options.index(active_key.name)
    return 0


def _provider_for(style: ReportConfig, key: ApiKeyEntry | None) -> str:
    candidate = key.provider if key else style.llm.provider
    return candidate if candidate in PROVIDER_DEFAULTS else 'openai'


def _model_for(provider: str, style: ReportConfig, key: ApiKeyEntry | None) -> str:
    if key and key.provider == provider:
        return key.model
    if style.llm.provider == provider:
        return style.llm.model
    return PROVIDER_DEFAULTS[provider]['model']


def _base_url_for(provider: str, style: ReportConfig, key: ApiKeyEntry | None) -> str:
    if key and key.provider == provider:
        return key.base_url
    if style.llm.provider == provider:
        return style.llm.base_url
    return PROVIDER_DEFAULTS[provider]['base_url']
