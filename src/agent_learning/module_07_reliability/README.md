# 模块七：Agent 可靠性

Agent 不仅要能完成任务，还要能够应对网络抖动、限流、超时和外部工具暂时不可用等情况。本模块学习超时、有限重试、指数退避和错误分类。

## 第一节：基础重试

学习文件：[retry_basics.py](retry_basics.py)。

重试循环的核心顺序：

```text
执行操作
  -> 成功：立即返回
  -> 临时错误：判断是否还有机会
       -> 有：记录日志，进入下一次循环
       -> 无：重新抛出原异常
```

只应重试可能自行恢复的错误，例如网络超时、HTTP 429、HTTP 5xx。参数校验失败、工具不存在和权限不足通常不能靠原样重试解决。

完成四个 TODO 后运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_07_reliability.retry_basics
```

`FlakyTool` 的前两次调用会抛出 `TemporaryToolError`，第三次成功，因此最终结果中的 `attempts` 应该等于 `3`。

## 第二节：指数退避

学习文件：[exponential_backoff.py](exponential_backoff.py)。

如果失败后立即连续重试，可能会进一步压垮正在故障的服务。指数退避让等待时间逐次翻倍：

```python
base_delay * (2 ** (attempt - 1))
```

运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_07_reliability.exponential_backoff
```

默认 `base_delay=0.2`，工具第四次成功，因此依次等待 `0.2、0.4、0.8` 秒。`sleep_function` 可以在测试中替换真实的 `sleep()`。

## 第三节：退避上限和随机抖动

学习文件：[backoff_with_jitter.py](backoff_with_jitter.py)。

无限指数增长会导致等待过久，因此先使用 `min()` 添加上限：

```python
capped_delay = min(raw_delay, max_delay)
```

如果许多 Agent 同时失败，并使用完全相同的固定等待时间，它们也会同时再次请求。Full jitter 会在 `0` 到退避上限之间随机选择实际等待时间，从而分散请求：

```python
delay_seconds = jitter_function(0, capped_delay)
```

完成三个 TODO 后运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_07_reliability.backoff_with_jitter
```

默认参数下，四次失败对应的退避上限依次是 `0.2、0.4、0.5、0.5` 秒，实际等待时间会在各自的 `0` 到上限之间随机变化。

## 第四节：模型请求超时

学习文件：[model_timeout.py](model_timeout.py)。

重试只能限制“尝试多少次”，不能限制一次请求会卡多久。因此每次外部请求还需要设置 timeout。本节使用 OpenAI 兼容 Python SDK 的请求级配置：

```python
request_client = llm.client.with_options(
    timeout=timeout_seconds,
    max_retries=0,
)
```

这里返回的是一个带有本次配置的客户端副本，不会永久修改 `llm.client`。暂时设置 `max_retries=0`，是为了由我们自己的代码统一决定是否重试，避免 SDK 内置重试和外层重试叠加。

超时时 SDK 会抛出 `APITimeoutError`。完成三个 TODO 后运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_07_reliability.model_timeout
```

正常验证可以使用 `timeout_seconds=10.0`；学习超时分支时可以临时传入很小的值，但不要依赖真实网络稳定复现，后续会用假客户端进行确定性测试。

## 第五节：异常分类与重试决策

学习文件：[error_policy.py](error_policy.py)。

重试之前必须先判断错误是否可能自行恢复：

| 错误类型 | 是否重试 | 原因 |
| --- | --- | --- |
| `APITimeoutError` | 是 | 下次请求可能及时返回 |
| `APIConnectionError` | 是 | 网络连接可能恢复 |
| `RateLimitError` | 是 | 等待退避后配额可能恢复 |
| `InternalServerError` | 是 | 服务端临时故障可能恢复 |
| `TemporaryToolError` | 是 | 工具声明为临时故障 |
| `ValueError` 或参数校验错误 | 否 | 原样重试不会改变错误参数 |
| 认证、权限错误 | 否 | 需要修改凭据或权限配置 |

核心判断使用：

```python
isinstance(error, RETRYABLE_ERRORS)
```

完成三个 TODO 后运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_07_reliability.error_policy
```

示例中的第一次调用抛出临时工具错误，第二次成功，因此最终调用次数应为 `2`。对于不允许重试的异常，即使 `max_attempts=3`，也应该只调用一次。
