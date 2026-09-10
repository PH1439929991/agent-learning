"""练习：模型直接回答时，Agent 应在第一轮结束且不产生 tool 消息。"""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from agent_learning.module_04_tool_schema import agent


def test_agent_returns_direct_answer_without_tool(monkeypatch):
    """模拟一次没有 tool_calls 的模型回复，检查 Agent 的直接回答分支。"""
    final_answer = "你好，很高兴认识你。"

    # 模拟模型直接返回文本，没有要求调用任何工具。
    assistant_message = SimpleNamespace(
        role="assistant",
        content=final_answer,
        tool_calls=None,
    )

    # 记录 Agent 实际向模型发送了几次请求，以及每次请求的内容。
    requests = []

    def fake_create(**kwargs):
        requests.append(deepcopy(kwargs))

        # 正确情况下只会执行一次；如果再次请求，立即让测试失败。
        if len(requests) > 1:
            pytest.fail("模型已经直接回答，Agent 不应该再次请求模型")

        return SimpleNamespace(
            choices=[SimpleNamespace(message=assistant_message)]
        )

    fake_llm = SimpleNamespace(
        model="fake-model",
        temperature=0,
        client=SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=fake_create)
            )
        ),
    )

    def fake_llm_client():
        return fake_llm

    # 只替换模型客户端；ask_agent() 的循环仍然是真实代码。
    monkeypatch.setattr(agent, "LLMClient", fake_llm_client)

    answer = agent.ask_agent("你好", max_tool_rounds=3)

    # TODO：你来完成下面四项检查，然后删除 pytest.skip()。
    # 1. answer 等于 final_answer。
    # 2. requests 的长度等于 1。
    # 3. 第一次请求的 messages 长度等于 2（system + user）。
    # 4. messages 中不存在 role 为 "tool" 的消息。
    #
    assert answer == final_answer
    assert len(requests) == 1
    assert len(requests[0]["messages"]) == 2
    # 第 4 项提示：
    messages = requests[0]["messages"]
    assert all(message["role"] != "tool" for message in messages)
