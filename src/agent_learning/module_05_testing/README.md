# 模块五：自动化测试

模块五已完成，共有 10 个测试，覆盖工具执行器、直接回答、单次工具调用、同一轮多个工具、连续多轮工具和最大轮次保护。被测试的业务代码仍在模块四的 `agent.py`。

## 学习顺序

1. 阅读 `test_query_champion_success()`，理解准备输入、执行函数、断言结果。
2. 阅读 `test_invalid_argument_never_executes_tool()`，理解如何确认校验失败后工具没有被执行。
3. 阅读已完成的练习一：检查可选地区的默认值是否真的传入工具。
4. 阅读已完成的练习二：检查未注册工具返回失败。
5. 阅读已完成的练习三：非法 JSON 返回错误，而且不能执行工具。
6. 完成 `test_agent_loop.py` 中的断言：最终答案、两次模型请求、第二次请求中的工具结果。
7. 完成 `test_agent_direct_answer.py`：验证模型直接回答时只请求一次，并且不产生 tool 消息。
8. 完成 `test_agent_multiple_tools.py`：验证模型同一轮返回两个工具调用时，两条工具结果都进入第二次请求。
9. 完成 `test_agent_sequential_tools.py`：验证模型连续两轮调用工具时，请求消息从 2 条增长到 4 条、6 条。
10. 完成 `test_agent_max_rounds.py`：使用 `pytest.raises` 验证达到最大轮次后抛出异常并停止请求。

`assert` 条件不成立时，pytest 会把该用例标记为失败，并展示差异。只打印结果、或者只检查程序没有报错，不能证明结果正确。

`monkeypatch` 是 pytest 提供的测试辅助对象。这里用它临时替换注册表中的函数，记录调用；测试结束后会自动恢复，避免影响其他用例。

## 运行

首次安装测试依赖：

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

在仓库根目录运行整个模块：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_05_testing -v
```

只运行第一个示例：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_05_testing/test_tool_executor.py::test_query_champion_success -v
```

2026-09-07 已完成两个练习并删除 `pytest.skip()`，实测结果为 `4 passed`。初始的 `2 passed, 2 skipped` 只表示两个示例通过；跳过不等于通过。

复习见[今晚学习总结](../../../work/2026-09-07-自动化测试学习总结.md)。

## 下一章

继续学习 `module_06_observability`：使用日志记录 Agent 的模型请求、工具执行、耗时和 Token。这里的离线测试验证程序行为；真实模型能否正确选择工具，需要另设模型评测用例。

参考：[pytest 入门](https://docs.pytest.org/en/stable/getting-started.html)、[monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)。
