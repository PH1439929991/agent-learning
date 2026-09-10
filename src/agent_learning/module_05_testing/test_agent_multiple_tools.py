"""练习：模型在同一轮返回两个工具调用，Agent 应全部执行。"""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from agent_learning.module_04_tool_schema import agent


def make_tool_call(call_id: str, champion_name: str) -> SimpleNamespace:
    """构造一次模拟的英雄查询工具调用。"""
    return SimpleNamespace(
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


def test_agent_executes_two_tools_from_one_model_reply(monkeypatch):
    # 模型第一次回复中，同时要求查询两个英雄。
    yasuo_call = make_tool_call("call_yasuo_001", "亚索")
    kennen_call = make_tool_call("call_kennen_002", "凯南")

    first_message = SimpleNamespace(
        role="assistant",
        content=None,
        tool_calls=[yasuo_call, kennen_call],
    )

    # 两个工具结果都返回模型后，模型给出最终回答。
    final_answer = "亚索和凯南都来自艾欧尼亚。"
    second_message = SimpleNamespace(
        role="assistant",
        content=final_answer,
        tool_calls=None,
    )

    replies = [first_message, second_message]
    requests = []

    def fake_create(**kwargs):
        requests.append(deepcopy(kwargs))
        if not replies:
            pytest.fail("预期只请求模型两次，Agent 却继续请求了")

        return SimpleNamespace(
            choices=[SimpleNamespace(message=replies.pop(0))]
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

    monkeypatch.setattr(agent, "LLMClient", lambda: fake_llm)

    answer = agent.ask_agent("分别介绍亚索和凯南", max_tool_rounds=3)

    # 第二次请求模型时，消息顺序应该是：
    # system、user、assistant(tool_calls)、tool(亚索)、tool(凯南)。
    second_messages = requests[1]["messages"]
    yasuo_tool_message = second_messages[3]
    kennen_tool_message = second_messages[4]

    yasuo_result = json.loads(yasuo_tool_message["content"])
    kennen_result = json.loads(kennen_tool_message["content"])

    # TODO：完成下面六项检查，然后删除 pytest.skip()。
    # 1. answer 等于 final_answer。
    # 2. 一共请求模型两次。
    # 3. 第二次请求包含五条 messages。
    # 4. 两条 tool 消息的 tool_call_id 分别匹配 yasuo_call 和 kennen_call。
    # 5. yasuo_result 查询到的中文名是“亚索”。
    # 6. kennen_result 查询到的中文名是“凯南”。
    assert answer == final_answer
    assert len(requests) == 2
    assert len(requests[1]["messages"]) == 5
    #这里应该用的second做判断
    assert yasuo_tool_message["tool_call_id"] == yasuo_call.id
    assert kennen_tool_message["tool_call_id"] == kennen_call.id
    assert yasuo_result["champion_data"]["name_cn"] == "亚索"
    assert kennen_result["champion_data"]["name_cn"] == "凯南"
