# Python Agent 应用开发学习路线

> 适用对象：有后端基础，希望使用 Vibe Coding，在 14 天内完成一个可运行、可测试、可部署的 Python Agent 应用 MVP。

## 1. 半个月的目标

半个月足够完成一个完整 MVP，但不以“掌握所有 Agent 技术”为目标。

建议最终完成一个“个人知识与任务 Agent”，支持：

- 流式、多轮对话；
- 上传并检索 Markdown、PDF 等资料；
- 根据资料回答问题并保留来源；
- 调用搜索笔记、创建待办等工具；
- 写操作前请求用户确认；
- 保存会话和工具执行记录；
- 记录耗时、Token 和调用次数；
- 运行固定的自动化评测；
- 通过 Web API 或简单页面对外提供服务。

Agent 可以理解为：

```text
Agent = 模型 + 指令 + 工具 + 循环 + 状态 + 权限边界 + 评测
```

## 2. Python 技术栈

- Python 3.12+
- uv：项目、虚拟环境和依赖管理
- OpenAI Python SDK
- Responses API
- Pydantic：工具参数和输出校验
- FastAPI：HTTP API
- SQLAlchemy 2.0：数据访问
- SQLite：学习阶段的本地数据库
- PostgreSQL + pgvector：正式项目阶段再引入
- pytest：单元测试与 Agent 评测
- Ruff：代码检查和格式化
- mypy 或 pyright：类型检查

前端不是半个月内的重点。第一版可以使用命令行，第二版通过 FastAPI 提供接口；有余力再添加简单聊天页面。

## 3. 核心学习顺序

```text
模型调用
  ↓
结构化输出与流式响应
  ↓
Function Calling
  ↓
Agent Loop
  ↓
会话状态与记忆
  ↓
RAG 文档检索
  ↓
安全和权限控制
  ↓
评测与可观测性
  ↓
FastAPI 产品化
  ↓
多 Agent（进阶）
```

### 3.1 最小模型调用

先完成一个命令行聊天程序：

```text
用户输入问题 → 调用 Responses API → 打印回答
```

需要掌握：

- 从环境变量读取 API Key；
- 创建 OpenAI 客户端；
- 设置模型指令和用户输入；
- 获取普通输出和流式输出；
- 处理超时、限流和请求失败；
- 记录耗时与 Token。

完成标准：

```bash
uv run python -m src.main
```

运行后可以在终端连续问答。

### 3.2 Function Calling

为 Agent 添加查询笔记、读取时间或创建待办等真实工具。

```text
用户提出任务
  ↓
模型判断是否调用工具
  ↓
Pydantic 校验工具参数
  ↓
Python 函数执行真实操作
  ↓
将工具结果返回模型
  ↓
模型生成最终回答
```

需要实现：

- 工具注册表；
- Pydantic 参数模型；
- 通用工具执行器；
- 统一的成功和错误返回结构；
- 最大调用次数、超时与重试；
- 副作用操作的用户确认。

### 3.3 手写 Agent Loop

在使用高级 Agent 框架前，至少手写一次循环：

```python
steps = 0

while not finished and steps < max_steps:
    response = call_model(context=context, tools=tools)

    if response_requires_tool(response):
        result = execute_tool(response)
        context.append(result)
    else:
        finished = True

    steps += 1
```

需要理解：

- Agent 在什么条件下结束；
- 工具失败后是否重试；
- 如何防止无限循环；
- 如何避免重复执行写操作；
- 多个工具如何串联；
- 如何记录每一步执行轨迹。

### 3.4 状态与记忆

记忆不等于把全部历史消息无限发送给模型。建议分为：

- 短期状态：当前任务已经执行的步骤和结果；
- 会话记忆：最近几轮对话和用户选择；
- 长期记忆：用户偏好、历史任务和知识内容。

数据库至少设计：

- `conversations`：会话；
- `messages`：消息；
- `agent_runs`：Agent 运行记录；
- `tool_calls`：工具调用记录；
- `documents`：知识库文档及元数据。

同时处理长对话压缩、数据过期策略和用户隔离。

### 3.5 RAG 文档检索

```text
文档 → 解析 → 切分 → 建立索引 → 检索片段 → 模型回答并引用来源
```

重点关注：

- Markdown、PDF 如何解析；
- 文档如何合理切分；
- 检索结果是否真正相关；
- 如何保留文件名和片段来源；
- 没找到答案时如何明确拒答；
- 用户是否有权查看检索到的文档；
- 如何评估检索准确率。

学习阶段优先使用托管的文件检索能力，理解流程后再研究 PostgreSQL + pgvector。

### 3.6 FastAPI 产品化

推荐调用链：

```text
浏览器或 API 客户端
  ↓
FastAPI
  ↓
Agent Runtime
  ↓
模型 / 工具 / 数据库
```

依次实现：

1. `POST /chat` 单轮聊天；
2. SSE 流式响应；
3. 多轮会话；
4. 工具调用状态事件；
5. 取消正在运行的任务；
6. 历史会话查询；
7. 文件上传；
8. 用户身份与数据隔离；
9. 写操作确认接口。

### 3.7 安全和权限

| 操作类型 | 示例 | 建议策略 |
| --- | --- | --- |
| 只读操作 | 搜索、查询、分析 | 可自动执行 |
| 可恢复写入 | 创建草稿、创建待办 | 展示执行状态 |
| 外部写入 | 发邮件、发消息、提交数据 | 执行前明确确认 |
| 高风险操作 | 删除、付款、部署、修改权限 | 二次确认并记录审计日志 |

必须遵守：

- 所有工具参数都用 Pydantic 在服务端校验；
- API Key 只保存在服务端环境变量；
- 不允许模型直接执行任意 Python、Shell 或 SQL；
- SQL 查询使用参数绑定；
- 写操作实现幂等键或防重复机制；
- 每个工具设置超时和调用上限；
- 用户只能访问自己的数据；
- 外部写入和高风险操作留下审计记录。

### 3.8 评测与可观测性

不要只依赖人工聊天测试。建立固定测试集：

```json
{
  "input": "找出笔记里关于 Python 异步编程的内容",
  "expected_tool": "search_notes",
  "must_include": ["asyncio"],
  "must_not_call": ["delete_note"]
}
```

至少检查：

- 最终回答是否正确；
- 是否选择正确工具；
- 工具参数是否正确；
- 是否编造不存在的内容；
- 是否出现越权调用；
- 任务成功率、延迟和 Token 成本；
- 工具调用次数与重试次数。

每次修改 Prompt、工具描述、模型或检索策略，都运行同一批测试。

### 3.9 多 Agent

只有单 Agent 已经稳定，并且评测证明拆分有收益时，再学习路由、handoff、专家 Agent 和并行执行。

```text
研究任务
├── 搜索 Agent
├── 数据分析 Agent
└── 报告 Agent
```

如果一个 Agent 加几个工具已经能够完成，或者步骤之间高度依赖，就不需要拆成多 Agent。

## 4. 14 天 Python 编码计划

按每天投入 3～4 小时设计。每天 2 小时可以完成基础 Demo；每天 6 小时以上可以进一步完善评测、权限和部署。

| 时间 | 学习与编码内容 | 当天交付物 |
| --- | --- | --- |
| 第 1 天 | uv、Python 项目结构、Responses API、环境配置 | 命令行聊天程序 |
| 第 2 天 | Prompt、Pydantic 结构化输出、流式响应 | 流式输出和结构化返回 |
| 第 3 天 | Function Calling | 第一个只读 Python 工具 |
| 第 4 天 | 工具注册、参数校验、异常处理 | 通用工具执行器 |
| 第 5 天 | 手写 Agent Loop | 自动连续调用工具 |
| 第 6 天 | 最大步数、超时、重试和终止条件 | 可控的单 Agent |
| 第 7 天 | SQLAlchemy、SQLite、会话和消息存储 | 多轮会话 |
| 第 8 天 | 文档解析、切分、检索和引用 | 简单 RAG |
| 第 9 天 | 文件上传和知识库查询 | 文档问答 Agent |
| 第 10 天 | FastAPI 接口和 SSE 流式响应 | HTTP API 版本 |
| 第 11 天 | 工具状态事件和任务中止 | 完整执行链路 |
| 第 12 天 | 写操作确认、权限和安全边界 | 安全的写工具 |
| 第 13 天 | pytest 测试集和自动化评测 | Evals 脚本与报告 |
| 第 14 天 | 日志、成本统计、容器化、部署和文档 | 可演示的 Agent MVP |

建议时间分配：

- 20% 阅读官方文档；
- 70% 编码与调试；
- 10% 评测与复盘。

## 5. Vibe Coding 工作方法

AI 可以辅助生成约 80%～90% 的代码，但开发者仍负责需求、架构、验收和风险判断。

### 5.1 适合交给 AI

- 初始化 uv 和 Python 项目；
- 接入 OpenAI Python SDK；
- 实现流式聊天和 Function Calling；
- 创建 SQLAlchemy 模型和数据访问层；
- 编写 RAG 流程；
- 创建 FastAPI 接口；
- 编写 pytest 测试与评测；
- 分析并修复报错；
- 完善 README、Dockerfile 和部署配置。

### 5.2 必须自己理解

1. 一次模型请求如何进入和返回；
2. 模型为什么选择某个工具；
3. 工具结果如何传回模型；
4. Agent Loop 为什么结束；
5. 会话状态存在哪里；
6. 写操作如何获得用户确认；
7. 如何验证最终结果是否正确。

### 5.3 每个功能的工作循环

```text
1. 让 AI 阅读当前项目和约束
2. 给出当前功能的验收标准
3. 每次只实现一个小功能
4. 自动运行 Ruff、类型检查和 pytest
5. 让 AI 解释关键数据流与风险
6. 自己实际操作验收
7. 提交一次 Git commit
```

### 5.4 第一个 Vibe Coding 提示词

```text
请检查当前项目，实现一个最小的 OpenAI Responses API 命令行程序。

要求：
1. 使用 Python 3.12 和 uv。
2. 使用 src layout。
3. 从环境变量读取 API Key，提供 .env.example，但不要提交真实密钥。
4. 支持命令行连续输入。
5. 输出模型回答，并提供可选的流式输出。
6. 加入清晰的错误处理和日志。
7. 使用 Ruff、类型检查和 pytest。
8. 补充安装与运行说明。
9. 完成后运行所有检查。
10. 暂时不要实现工具调用、数据库和 Web 页面。
```

第二个任务：

```text
在现有 Python 项目中加入 get_current_time 工具。

要求：
1. 使用 Pydantic 定义和校验工具参数。
2. 实现完整的 Function Calling 循环。
3. 设置最大执行步数、超时和明确的错误返回。
4. 保留现有功能并补充 pytest。
5. 完成后解释从用户请求到工具结果返回模型的完整数据流。
```

每次功能完成后的复盘：

```text
请按照请求入口、模型调用、工具执行、状态保存和错误处理五个部分，
向有后端基础的 Python 开发者解释本次实现，并指出我必须亲自检查的三处代码。
```

## 6. 推荐项目结构

```text
agent-learning/
├── src/
│   └── agent_learning/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── agent/
│       │   ├── runner.py
│       │   ├── instructions.py
│       │   └── models.py
│       ├── tools/
│       │   ├── registry.py
│       │   ├── search_notes.py
│       │   └── create_task.py
│       ├── memory/
│       │   ├── models.py
│       │   └── repository.py
│       ├── rag/
│       │   ├── loader.py
│       │   ├── splitter.py
│       │   └── retriever.py
│       ├── api/
│       │   ├── app.py
│       │   └── routes.py
│       └── evals/
│           ├── cases.json
│           └── runner.py
├── tests/
├── migrations/
├── .env.example
├── .gitignore
├── pyproject.toml
├── Dockerfile
└── README.md
```

## 7. 推荐 Git 提交顺序

1. `init python project with uv`
2. `add first responses api call`
3. `add streaming output`
4. `add function calling`
5. `implement agent loop`
6. `add conversation storage`
7. `add document search`
8. `add agent evals`
9. `add fastapi interface`
10. `add approval and permission controls`

## 8. 半个月内暂不投入

- 复杂多 Agent 编排；
- 模型微调；
- 自行实现向量数据库；
- 重型工作流框架；
- MCP Server 开发；
- 语音和实时通信；
- 浏览器自动化；
- 复杂前端视觉设计。

先让一个 Python 单 Agent 的工具调用、状态、权限和评测稳定，再逐步扩展。

## 9. MVP 完成检查表

- [ ] 项目可通过 uv 从零安装并启动；
- [ ] API Key 只通过环境变量配置；
- [ ] Ruff、类型检查和 pytest 全部通过；
- [ ] 支持流式和多轮对话；
- [ ] 至少包含一个只读工具和一个写入工具；
- [ ] 工具参数经过 Pydantic 校验；
- [ ] Agent Loop 有最大步数和超时；
- [ ] 写入操作需要用户确认；
- [ ] 会话和工具调用能够持久化；
- [ ] 文档回答包含来源；
- [ ] 有一组固定自动化评测；
- [ ] 能记录错误、耗时、Token 和调用次数；
- [ ] README 包含安装、配置、启动和测试说明；
- [ ] 应用已部署或可通过统一命令运行。

完成这些检查后，再进入多 Agent、MCP、实时语音和复杂工作流阶段。
