# Agent 应用开发学习项目

学习代码按模块分目录；历史学习总结保留在 `work/`。

## 当前学到哪里

**当前模块：模块六，日志与可观测性。**

模块五已完成 10 个离线测试。现在从 [logging_basics.py](src/agent_learning/module_06_observability/logging_basics.py) 开始学习日志级别和统一格式，详细说明见[模块六](src/agent_learning/module_06_observability/README.md)。

| 想改的内容 | 打开哪个文件 |
| --- | --- |
| 当前日志基础练习 | [logging_basics.py](src/agent_learning/module_06_observability/logging_basics.py) |
| 已完成的自动化测试 | [module_05_testing](src/agent_learning/module_05_testing/) |
| 工具参数类型、必填规则、默认值 | [argument_models.py](src/agent_learning/module_04_tool_schema/argument_models.py) |
| 将参数模型转换成工具说明 | [schema_builder.py](src/agent_learning/module_04_tool_schema/schema_builder.py) |
| 工具注册、模型请求、校验错误反馈、Agent 循环 | [agent.py](src/agent_learning/module_04_tool_schema/agent.py) |
| 实际查询英雄、按地区返回列表 | [champion_tools.py](src/agent_learning/module_03_function_calling/champion_tools.py) |
| 模型客户端和环境变量加载 | [llm_client.py](src/agent_learning/common/llm_client.py) |
| 英雄和地区资料 | `src/agent_learning/data/` |

模块四已完成：注册表生成工具 schema、参数校验和错误反馈；连续工具调用的真实模型用例也已通过。模块五将这些行为逐步变成可重复执行的测试。

## 目录与学习顺序

```text
src/agent_learning/
├── common/
│   └── llm_client.py                 # 共享模型客户端
├── module_01_llm_basics/             # 模块一：模型基础
│   ├── system_prompt.py
│   ├── streaming.py
│   └── usage_metrics.py
├── module_02_context/                # 模块二：上下文管理
│   ├── context_trimming.py
│   └── multi_turn_chat.py
├── module_03_function_calling/       # 模块三：工具调用基础
│   ├── champion_tools.py            # 真实工具函数
│   └── single_tool_agent.py         # 单工具版本，供回顾
├── module_04_tool_schema/            # 模块四：参数校验和 schema
│   ├── argument_models.py           # 参数模型 + 离线练习
│   ├── schema_builder.py            # schema 生成 + 离线检查
│   └── agent.py                     # 当前多工具集成入口
├── module_05_testing/                # 模块五：自动化测试（已完成）
│   ├── test_tool_executor.py
│   └── test_agent_*.py
├── module_06_observability/          # 模块六：当前学习模块
│   └── logging_basics.py             # 日志基础练习
├── data/
│   ├── champions.json
│   └── regions.json
├── .env                             # 本地配置，不提交 Git
└── .env.example                     # 配置模板
work/                                # 历史学习笔记
```

每个代码目录里的 `__init__.py` 是 Python 包标识文件，不是练习入口。

## 运行方法

以下命令在仓库根目录 `agent-learning/` 执行，适用于 macOS / Linux。

新电脑首次准备环境：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

需要请求模型时，把 `.env.example` 的内容复制到同目录的 `.env`，填写自己的配置。已有 `.env` 的电脑继续使用原文件。

我们统一使用 `PYTHONPATH=src` 和 `python -m` 运行：前者告诉 Python 从哪里找项目包，后者按照模块路径启动文件，保证跨目录导入正确。模块路径使用点号，不带 `.py`。

当前模块的离线测试（首次需要安装开发依赖）：

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_05_testing -v
```

模块四的两个离线练习，无需调用模型：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_04_tool_schema.argument_models
PYTHONPATH=src .venv/bin/python -m agent_learning.module_04_tool_schema.schema_builder
```

当前多工具 Agent（提问后会请求配置的模型 API）：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_04_tool_schema.agent
```

回顾以前的模块：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_01_llm_basics.system_prompt
PYTHONPATH=src .venv/bin/python -m agent_learning.module_01_llm_basics.streaming
PYTHONPATH=src .venv/bin/python -m agent_learning.module_01_llm_basics.usage_metrics
PYTHONPATH=src .venv/bin/python -m agent_learning.module_02_context.context_trimming
PYTHONPATH=src .venv/bin/python -m agent_learning.module_02_context.multi_turn_chat
PYTHONPATH=src .venv/bin/python -m agent_learning.module_03_function_calling.single_tool_agent
```

其中 `context_trimming` 是本地演示；其他回顾入口涉及模型请求。不要再使用历史笔记中的旧文件启动命令，以本页为准。

## 旧文件名在哪里

| 旧文件名 | 新位置（相对于 `src/agent_learning/`） |
| --- | --- |
| `LLM_client.py` | `common/llm_client.py` |
| `system_prompt_lab.py` | `module_01_llm_basics/system_prompt.py` |
| `streaming_comparison.py` | `module_01_llm_basics/streaming.py` |
| `usage_metrics_exercise.py` | `module_01_llm_basics/usage_metrics.py` |
| `context_window_management.py` | `module_02_context/context_trimming.py` |
| `multi_turn_chat.py` | `module_02_context/multi_turn_chat.py` |
| `champion_agent.py` | `module_03_function_calling/single_tool_agent.py` |
| `champions_tools.py` | `module_03_function_calling/champion_tools.py` |
| `pydantic_tool_validation_exercise.py` | `module_04_tool_schema/argument_models.py` |
| `pydantic_schema_exercise.py` | `module_04_tool_schema/schema_builder.py` |
| `multi_tool_agent.py` | `module_04_tool_schema/agent.py` |

以后继续学习时，先打开当前模块的目录，再按上方职责表定位文件。
