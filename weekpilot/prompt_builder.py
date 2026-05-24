"""Build prompts from weekly inputs and style settings."""

from __future__ import annotations

import json

from weekpilot.models import CollectedInputs, PromptBundle, model_to_dict
from weekpilot.privacy import sanitize_text


def build_prompt_from_inputs(inputs: CollectedInputs) -> PromptBundle:
    """Build a prompt directly from local input files, then apply privacy masking."""

    developer_prompt = (
        '你是 WeekPilot，一个本地周报生成助手。'
        '你的任务是把用户提供的本地工作材料整理成可直接编辑和发送的中文周报。'
        '你必须严格基于输入材料生成事实内容。'
        '允许在表达层进行专业化润色、归纳和合理的价值提炼，但不得新增输入中没有的事实、数字、结论、负责人、日期或承诺。'
        '如果信息不足，必须写“待确认”或“待补充”，不能自行推断。'
        '输出必须是合法 JSON 对象，不要使用 Markdown 代码块，不要输出 JSON 之外的任何文字。'
    )
    config_payload = model_to_dict(inputs.style)
    user_prompt = f"""
请根据以下配置和原始工作材料生成中文周报。

输出格式：
必须只输出一个合法 JSON 对象，字段必须完整，字段值均为字符串。JSON 字符串内部可以包含 Markdown 换行。

{{
  "standard": "...",
  "short": "...",
  "detailed": "...",
  "retro": "...",
  "next_week_todo": "..."
}}

输入来源说明：
- weekly_log.md：优先用于本周进展、完成事项、进行中事项、问题和下周计划。
- tasks.csv：优先用于任务状态、未完成事项、阻塞、优先级和截止时间。
- meeting_notes.md：优先用于重要决策、协作事项、待确认问题和风险。

表达优化目标：
- 你不是简单复述输入材料，而是要把零散工作记录整理成更专业、完整、可提交的周报表达。
- 可以在不新增事实的前提下，对输入内容进行归纳、合并、改写和结构化表达。
- 可以补充合理的工作价值描述，例如“提升对齐效率”“降低后续联调风险”“为后续方案细化提供依据”，但必须能从输入材料中自然推出。
- 可以将口语化、碎片化、TODO 式记录改写成正式、清晰、结果导向的工作描述。
- 对同类工作应适当合并，避免逐条机械罗列。
- 对关键事项应补充“背景 / 动作 / 结果 / 影响 / 下一步”中的相关信息；如果材料不足，用“待补充”或“待确认”。

润色与扩写边界：
- 可以优化措辞、调整结构、补足上下文连接、提炼价值和风险。
- 不可以编造具体数字、完成比例、负责人、日期、会议结论、业务结果或外部承诺。
- 不要为了显得丰富而增加空泛套话。
- 不要使用“显著提升”“全面完成”“重大突破”等没有证据支撑的表述。
- 不要把不确定事项写成已经完成的事实。

内容密度要求：
- 每个主要章节优先保留 3 到 6 条高质量内容。
- 单条内容尽量控制在 1 到 2 句话。
- 优先写清楚交付物、协作对象、当前状态、风险和下一步。
- 少用形容词，多用具体动作和结果。

通用写作要求：
- 使用中文，面向直属负责人或项目相关方。
- 结果导向，少用空泛形容词，多写动作、对象、交付物和下一步。
- 每条进展尽量包含“动作 + 对象 + 结果”。
- 风险与阻塞必须写清楚影响和下一步动作。
- 没有明确材料时写“待补充”或“待确认”，不要写不存在的内容。
- 不要夸大事实，不要使用“显著”“全面”“重大突破”等没有证据支撑的表达。
- 不要输出“根据你提供的材料”等寒暄句，直接给周报内容。

字段要求：
- standard：正式周报，必须包含二级标题：本周工作进展、主要产出、风险与阻塞、重要决策、下周计划、需要协同/确认的问题。
- short：适合 IM 或群消息，控制在 300 到 600 个中文字符，突出完成、风险和下周重点。
- detailed：适合发给负责人，比 standard 更详细，可补充背景、协作、风险影响和下一步动作。
- retro：个人复盘，必须包含：收获、问题、改进点。不要默认作为对外周报语气。
- next_week_todo：Markdown checklist，每行使用“- [ ] ”开头；只列可执行事项，避免泛泛而谈。

style_config:
{json.dumps(config_payload, ensure_ascii=False, indent=2)}

weekly_log.md:
{inputs.weekly_log.strip() or '（未提供）'}

tasks.csv:
{inputs.tasks_csv.strip() or '（未提供）'}

meeting_notes.md:
{inputs.meeting_notes.strip() or '（未提供）'}
""".strip()
    privacy = sanitize_text(user_prompt, inputs.style.privacy)
    return PromptBundle(
        developer_prompt=developer_prompt,
        user_prompt=user_prompt,
        sanitized_user_prompt=privacy.text,
        privacy=privacy,
    )
