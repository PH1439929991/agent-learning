"""Agent 循环练习：一次工具调用、两次模拟模型请求，不访问模型 API。"""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from agent_learning.module_04_tool_schema import agent


def test_agent_returns_tool_result_to_model(monkeypatch):
    # 1. 提前准备“模型第一次回复”：要求调用查询亚索的工具。
    tool_call = SimpleNamespace(
        id="call_yasuo_001",
        type="function",
        function=SimpleNamespace(
            name="get_champion_info",
            arguments=json.dumps({"champion_name": "亚索"}, ensure_ascii=False),
        ),
    )
    first_message = SimpleNamespace(
        role="assistant", content=None, tool_calls=[tool_call]
    )

    # 2. 第二次回复不再要求工具，表示模型已经给出最终答案。
    # 这是测试预设的文本，不是实际模型生成的回答。
    final_answer = "亚索是来自艾欧尼亚的疾风剑豪。"
    second_message = SimpleNamespace(
        role="assistant", content=final_answer, tool_calls=None
    )
    replies = [first_message, second_message]
    requests = []

    def fake_create(**kwargs):
        # 类似之前的 calls，记录每次请求模型时实际传入的参数。
        # messages 后续会被追加，所以深拷贝保存“请求当时”的快照。
        requests.append(deepcopy(kwargs))
        if not replies:
            pytest.fail("预期只请求模型两次，Agent 却继续请求了")
        # 第一次调用取 first_message，第二次调用取 second_message。
        message = replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    # 3. 构造与当前 LLMClient 访问方式一致的替身对象。
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

    # setattr 修改模块属性；之前的 setitem 修改字典键值。
    # 替换 agent 内使用的 LLMClient，避免创建真实客户端或请求网络。
    monkeypatch.setattr(agent, "LLMClient", fake_llm_client)

    # 4. 运行真实 Agent 循环和真实本地工具；只有模型是替身。
    answer = agent.ask_agent("请介绍亚索", max_tool_rounds=3)

    # 5. 先检查 Agent 最终返回值，以及总共请求模型的次数。
    assert answer == final_answer
    assert len(requests) == 2

    # 6. 第一次请求模型时，还只有 system 和 user 两条消息。
    first_request_messages = requests[0]["messages"]
    assert len(first_request_messages) == 2
    assert first_request_messages[0]["role"] == "system"
    assert first_request_messages[1] == {
        "role": "user",
        "content": "请介绍亚索",
    }

    # 7. 模型第一次要求调用工具后，Agent 会追加两条消息：
    # assistant 的工具调用 + 本地工具返回的 tool 消息。
    # 因此第二次请求时，messages 一共有四条。
    second_request_messages = requests[1]["messages"]
    assert len(second_request_messages) == 4

    assistant_tool_call_message = second_request_messages[2]
    assert assistant_tool_call_message.role == "assistant"
    assert assistant_tool_call_message.tool_calls[0].id == tool_call.id

    # 8. 最后一条是工具结果，它通过 tool_call_id 与上面的调用对应。
    tool_message = second_request_messages[3]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == tool_call.id

    # tool 消息的 content 是 JSON 字符串，先解析成字典再检查业务结果。
    tool_result = json.loads(tool_message["content"])
    assert tool_result["success"] is True
    assert tool_result["champion_data"]["name_cn"] == "亚索"
