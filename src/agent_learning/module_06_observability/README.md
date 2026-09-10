# 模块六：日志与可观测性

模块五已经用测试证明 Agent 的关键路径正确。模块六开始回答另一个问题：Agent 真正运行时，怎样知道它走到了哪一步、哪里失败、耗时多久、消耗了多少 Token。

## 第一节：logging 基础

当前学习文件：[logging_basics.py](logging_basics.py)。

`print()` 适合临时观察；`logging` 适合长期运行的程序，因为日志自带时间、级别和来源，还可以统一控制是否输出以及写到哪里。

常用级别：

| 级别 | 使用场景 |
| --- | --- |
| `DEBUG` | 开发时查看详细过程，例如请求参数构造 |
| `INFO` | 正常业务事件，例如 Agent 开始、工具执行成功 |
| `WARNING` | 可以继续运行，但出现异常情况，例如工具查询失败 |
| `ERROR` | 本次流程无法正常完成，例如模型请求异常 |

基本结构：

```python
import logging

logger = logging.getLogger(__name__)
logger.info("工具执行开始 | tool_name=%s", tool_name)
```

这里 `%s` 是日志占位符，后面的 `tool_name` 会在真正输出日志时填进去。

## 当前练习

在 `demonstrate_log_levels()` 中完成两个 TODO：

1. 使用 `logger.warning()` 记录工具返回失败和工具名。
2. 使用 `logger.error()` 记录达到最大轮次和轮次上限。

在项目根目录运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_06_observability.logging_basics
```

当前 `level=logging.INFO`，因此你应该看到 `INFO`、`WARNING`、`ERROR`，但看不到 `DEBUG`。

## 第二节：工具执行耗时

学习文件：[tool_timing.py](tool_timing.py)。

计时采用：

```python
start_time = perf_counter()
result = tool_function(**arguments)
end_time = perf_counter()
duration_ms = (end_time - start_time) * 1000
```

`perf_counter()` 的值本身不是当前时间；这里关心的是结束值减开始值。差值单位是秒，乘以 `1000` 后转换为毫秒。

完成文件中的三个 TODO 后运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_06_observability.tool_timing
```

预期依次看到工具开始、工具完成、结果交还调用方三条 `INFO` 日志。

下一步会处理工具抛出异常的情况，并使用 `logger.exception()` 记录错误堆栈。

## 第三节：工具异常日志

学习文件：[tool_error_logging.py](tool_error_logging.py)。

这一节用 `broken_tool()` 故意模拟工具失败，重点观察下面的执行顺序：

1. 记录工具开始日志。
2. 在 `try` 中调用工具。
3. 工具抛出异常，程序进入 `except`。
4. 计算工具失败前已经执行了多长时间。
5. 使用 `logger.exception()` 记录错误和 traceback。
6. 使用不带参数的 `raise`，把原异常继续交给上层调用方。

在 TODO 处补充：

```python
logger.exception(
    "工具执行异常 | tool_name=%s | duration_ms=%.2f | error=%s",
    tool_name,
    duration_ms,
    error,
)
```

然后运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_06_observability.tool_error_logging
```

`logger.exception()` 应当放在 `except` 代码块中。它不仅记录一条 `ERROR` 日志，还会自动记录异常类型、异常消息以及调用栈，方便定位工具在哪一行失败。

## 第四节：使用 request_id 串联日志

学习文件：[request_id_logging.py](request_id_logging.py)。

真实服务可能同时处理很多用户请求。如果日志里只有“工具执行开始”，我们无法判断它属于哪一次提问。解决办法是为每次 `ask_agent()` 调用生成一个唯一的 `request_id`，并把它传递给本次请求经过的每个函数。

完成三个 TODO：

1. 使用 `uuid4().hex[:8]` 生成 `request_id`。
2. 在工具开始执行前记录 `request_id`、工具名和参数。
3. 在 Agent 返回答案前记录 `request_id` 和答案。

运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_06_observability.request_id_logging
```

观察输出：同一次运行中的 Agent 开始、模型决定调用工具、工具开始、工具完成和 Agent 完成日志，应当具有完全相同的 `request_id`。

## 第五节：模型调用指标

学习文件：[llm_metrics_logging.py](llm_metrics_logging.py)。

这一节把第一章学过的 `response.usage` 接入日志系统。一次模型调用需要重点记录：

- `duration_ms`：模型响应耗时。
- `prompt_tokens`：输入给模型的 Token。
- `completion_tokens`：模型生成的 Token。
- `total_tokens`：本次请求的总 Token。
- `request_id`：这些指标属于哪一次 Agent 请求。

完成文件中的三个 TODO，然后运行一次真实模型请求：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_06_observability.llm_metrics_logging
```

如果服务商没有返回 `usage`，三个 Token 指标暂时记为 `0`。模型调用失败时，异常分支仍然应该记录失败前的耗时和 traceback。

## 第六节：累计整次 Agent 请求的指标

学习文件：[request_metrics.py](request_metrics.py)。

一次用户提问可能触发多轮模型调用和多次工具调用。每轮的 Token 都会产生实际消耗，所以请求汇总不能只保存最后一轮数据，而要使用 `+=` 累加。

练习模拟了三次模型调用，其中前两轮各调用一次工具。完成三个 TODO 后，最终指标应该是：

- 模型调用次数：`3`
- 工具调用次数：`2`
- 输入 Token：`540`
- 输出 Token：`90`
- 总 Token：`630`

运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_06_observability.request_metrics
```

注意：输入 Token 会随着对话历史和工具结果加入 `messages` 而增长。每轮请求都会重新处理本轮发送的完整上下文，因此这些输入 Token 都应该累计。
