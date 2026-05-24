# WeekPilot

WeekPilot 是一个本地运行的“数据驱动周报生成与工作复盘 Agent”。用户在一周中持续记录工作事项，周五下班前运行工具，系统读取本周工作日志、任务表和会议纪要，先按隐私配置做本地脱敏，再通过大模型生成可直接编辑和发送的周报。

## MVP 范围

- 只支持周报。
- 正式周报生成依赖大模型 API Key。
- 无 API Key 时可以使用 demo 模式预览流程，但 demo 输出会明确标记为演示内容。
- 暂不支持 docx 导出、账号系统、数据库和多人协作。

## 输入文件

默认读取 `input/`：

- `weekly_log.md`：本周工作日志。
- `tasks.csv`：任务表，字段为 `task,status,priority,due_date,note`。
- `meeting_notes.md`：会议纪要，可选。
- `style.yaml`：报告风格、模型和隐私脱敏配置。

`status` 推荐使用：

- `done`
- `in_progress`
- `todo`
- `blocked`

## 输出文件

默认写入 `output/`：

- `generation_meta.json`
- `weekly_report.md`
- `weekly_report_short.md`
- `weekly_report_detailed.md`
- `weekly_retro.md`
- `report_quality.md`
- `next_week_todo.md`

每次生成后还会复制到：

```text
output/history/<ISO-week>/
```

例如 `output/history/2026-W20/`，前端可以直接查看历史周报。

## 安装依赖

建议使用 Python 3.11+：

```bash
pip install -r requirements.txt
```

如果系统 `python` 不可用，也可以使用自己的虚拟环境或 `uv`。

## 配置 API Key

方式一：复制 `.env.example` 为 `.env`：

```bash
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.5
OPENAI_BASE_URL=https://api.openai.com/v1
```

如果使用 DeepSeek：

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

DeepSeek 走 OpenAI-compatible Chat Completions API。使用 `.env` 配置 DeepSeek 时，建议同步把 `input/style.yaml` 里的 `llm.provider` 改为 `deepseek`，或直接在 Streamlit 设置页添加 DeepSeek API Key 并激活。

方式二：在 Streamlit 的“设置”页面添加并激活 API Key。密钥会保存到本地 `config/api_keys.yaml`，该文件已被 `.gitignore` 忽略。

## 运行 CLI

生成示例输入：

```bash
python cli.py sample
```

使用正式 API 生成：

```bash
python cli.py generate --input-dir input --output-dir output
```

无 API Key 时查看演示流程：

```bash
python cli.py generate --input-dir input --output-dir output --demo
```

清空输出，保留 `.gitkeep`：

```bash
python cli.py clean-output
```

## 运行 Streamlit

```bash
streamlit run app.py
```

前端包含：

- 本周工作台：展示本周范围、输入状态、模型状态和生成结果。
- 历史周报：按周查看历史输出。
- 设置：管理 API Key、模型、周报风格和隐私脱敏。

## 隐私脱敏

WeekPilot 支持在发送给大模型前做本地脱敏：

- 自定义敏感词表。
- 常见邮箱、联系方式、URL、金额格式。
- 脱敏后保留语义角色，例如 `金额数据A`、`敏感词A`。

这是辅助能力，不是完整的数据防泄漏系统。建议在发送前预览并人工确认。

## 如何扩展成月报

后续可以增加：

- `report_type: monthly`
- 月度输入目录，例如 `input/monthly/2026-05/`
- 月报专用 prompt 和章节结构。
- 聚合多个周报历史目录生成月报。

核心模块可以复用：collector、prompt_builder、llm、critic、exporter、history。

## 每周五自动运行

Windows Task Scheduler 思路：

1. 创建基础任务，触发器选择每周五固定时间。
2. 操作选择启动程序。
3. 程序填写 Python 解释器路径。
4. 参数填写 `cli.py generate --input-dir input --output-dir output`。
5. 起始目录填写 WeekPilot 项目目录。

macOS/Linux cron 思路：

```cron
0 17 * * 5 cd /path/to/WeekPilot && python cli.py generate --input-dir input --output-dir output
```

如果使用虚拟环境，请在命令中使用虚拟环境里的 Python。

## 测试

```bash
pytest
```

如果 Windows 本机临时目录权限异常，可以改用：

```bash
pytest --basetemp .pytest-tmp
```

测试覆盖：

- sample input 抽取 completed / blocked / todo。
- demo provider 生成包含关键章节的周报。
- blocked / todo / in_progress 写入 `next_week_todo.md`。
