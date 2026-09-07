# 模块五：自动化测试

当前只修改 [test_tool_executor.py](test_tool_executor.py)。被测试的业务代码仍在模块四的 `agent.py`。

## 学习顺序

1. 阅读 `test_query_champion_success()`，理解准备输入、执行函数、断言结果。
2. 阅读 `test_invalid_argument_never_executes_tool()`，理解如何确认校验失败后工具没有被执行。
3. 阅读已完成的练习一：检查可选地区的默认值是否真的传入工具。
4. 阅读已完成的练习二：检查未注册工具返回失败。

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

## 后续内容

接下来再增加非法 JSON、错误参数重试、连续工具调用和最大轮次的测试，最后学习调用日志。这里的离线测试验证程序行为；真实模型能否正确选择工具，需要另设模型评测用例。

参考：[pytest 入门](https://docs.pytest.org/en/stable/getting-started.html)、[monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)。
