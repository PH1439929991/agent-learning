"""练习：模型连续两轮调用工具，第三轮才返回最终答案。"""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from agent_learning.module_04_tool_schema import agent


def make_tool_call(
    call_id: str,
    tool_name: str,
    arguments: dict,
) -> SimpleNamespace:
    """构造通用的模拟工具调用。"""
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name=tool_name,
            arguments=json.dumps(arguments, ensure_ascii=False),
        ),
    )


def test_agent_calls_tools_in_two_consecutive_rounds(monkeypatch):
    # 第一轮：模型先查询艾欧尼亚有哪些英雄。
    list_call = make_tool_call(
        "call_list_001",
        "list_champions",
        {"region": "艾欧尼亚"},
    )
    first_message = SimpleNamespace(
        role="assistant",
        content=None,
        tool_calls=[list_call],
    )

    # 第二轮：模型看到地区列表后，再查询亚索的详细资料。
    detail_call = make_tool_call(
        "call_detail_002",
        "get_champion_info",
        {"champion_name": "亚索"},
    )
    second_message = SimpleNamespace(
        role="assistant",
        content=None,
        tool_calls=[detail_call],
    )

    # 第三轮：模型不再调用工具，返回最终答案。
    final_answer = "艾欧尼亚包含亚索；亚索的称号是疾风剑豪。"
    third_message = SimpleNamespace(
        role="assistant",
        content=final_answer,
        tool_calls=None,
    )

    replies = [first_message, second_message, third_message]
    requests = []

    def fake_create(**kwargs):
        requests.append(deepcopy(kwargs))
        if not replies:
            pytest.fail("预期只请求模型三次，Agent 却继续请求了")

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

    answer = agent.ask_agent(
        "艾欧尼亚有哪些英雄？再介绍其中的亚索。",
        max_tool_rounds=4,
    )

    # 三次模型请求中的消息数量应依次是 2、4、6：
    # 第一次：system、user
    # 第二次：再加 first assistant、list tool
    # 第三次：再加 second assistant、detail tool
    second_messages = requests[1]["messages"]
    third_messages = requests[2]["messages"]

    list_tool_message = second_messages[3]
    detail_tool_message = third_messages[5]

    list_result = json.loads(list_tool_message["content"])
    detail_result = json.loads(detail_tool_message["content"])

    # TODO：完成下面七项检查，然后删除 pytest.skip()。
    # 1. answer 等于 final_answer。
    assert answer == final_answer
    # 2. requests 长度为 3。
    assert len(requests) == 3
    # 3. 第二次请求的 messages 长度为 4。
    assert len(second_messages) == 4
    # 4. 第三次请求的 messages 长度为 6。
    assert len(third_messages) == 6
    # 5. 两条 tool 消息分别匹配 list_call.id 和 detail_call.id。
    assert list_tool_message["tool_call_id"] == list_call.id
    assert detail_tool_message["tool_call_id"] == detail_call.id
    # 6. list_result 的 region 为“艾欧尼亚”，champions 包含“亚索”。
    assert list_result["region"] == "艾欧尼亚"
    assert any(
        champion["name_cn"] == "亚索"
        for champion in list_result["champions"]
    )
    # 7. detail_result 的英雄中文名为“亚索”。
    assert detail_result["champion_data"]["name_cn"] == "亚索"
