"""练习：达到最大工具轮次后，Agent 必须停止，防止无限循环。"""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from agent_learning.module_04_tool_schema import agent


def make_tool_message(call_id: str, champion_name: str) -> SimpleNamespace:
    """构造一条仍然要求调用工具的模拟模型回复。"""
    tool_call = SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name="get_champion_info",
            arguments=json.dumps(
                {"champion_name": champion_name},
                ensure_ascii=False,
            ),
        ),
    )
    message = SimpleNamespace(
        role="assistant",
        content=None,
        tool_calls=[tool_call],
    )
    return message



def test_agent_stops_after_max_tool_rounds(monkeypatch):
    # 两轮模型回复都要求继续调用工具，没有最终文本答案。
    first_message = make_tool_message("call_001", "亚索")
    second_message = make_tool_message("call_002", "凯南")
    replies = [first_message, second_message]

    requests = []
    executed_tool_ids = []

    def fake_create(**kwargs):
        requests.append(deepcopy(kwargs))
        if not replies:
            pytest.fail("Agent 不应该发起第 3 次模型请求")

        return SimpleNamespace(
            choices=[SimpleNamespace(message=replies.pop(0))]
        )

    def recording_execute_tool_call(tool_call):
        # 本测试只关心循环次数，所以用替身记录工具是否被执行。
        executed_tool_ids.append(tool_call.id)
        return {"success": True}

    fake_llm = SimpleNamespace(
        model="fake-model",
        temperature=0,
        client=SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=fake_create)
            )
        ),
    )

    monkeypatch.setattr(agent, "LLMClient", lambda: fake_llm)
    monkeypatch.setattr(
        agent,
        "execute_tool_call",
        recording_execute_tool_call,
    )

    # TODO 1：使用 pytest.raises 检查下面的调用会抛出 RuntimeError，
    # 并检查异常消息包含“工具调用轮次过多”。
    # 提示：
    # with pytest.raises(RuntimeError, match="工具调用轮次过多"):
    #     agent.ask_agent(...)
    #
    # 调用参数：问题写“继续调用工具”，max_tool_rounds=2。
    with pytest.raises(RuntimeError, match="工具调用轮次过多"):
        agent.ask_agent(
            "继续调用工具",
            max_tool_rounds=2,
        )
    # TODO 2：在 with 代码块之后完成两个断言：
    # 1. requests 长度为 2，证明没有第 3 次模型请求。
    # 2. executed_tool_ids 等于 ["call_001", "call_002"]，
    #    证明前两轮工具都正常执行了。
    assert len(requests) == 2
    assert executed_tool_ids == ["call_001", "call_002"]

    # 完成后删除函数上方的 @pytest.mark.skip 装饰器。
