"""第十八节：外部请求用替身，执行真实旧 Agent 循环和新检索工具。

test_exercise_* 在 TODO 未完成前失败是预期；没有真实 API 请求。
"""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent_learning.module_04_tool_schema import agent
from agent_learning.module_08_rag import rag_search_tool as lesson


def make_hits():
    return [
        {"chunk": {"chunk_id": "demo_000", "text": "练习角色住在示例地区。",
                   "embedding": [0.1, 0.2]}, "score": 0.9},
        {"chunk": {"chunk_id": "demo_001", "text": "当地有图书馆。"}, "score": 0.8},
    ]


def install_for_test(monkeypatch, retrieve):
    registry, tools = lesson.build_registration(retrieve)
    # 用 setattr 临时换成独立注册表，测试结束自动恢复；不修改旧文件。
    monkeypatch.setattr(agent, "TOOL_REGISTRY", registry)
    monkeypatch.setattr(agent, "TOOLS", tools)
    monkeypatch.setattr(agent, "SYSTEM_PROMPT", lesson.SYSTEM_PROMPT)


def make_call(arguments):
    return SimpleNamespace(id="call_search_001", type="function", function=SimpleNamespace(
        name="search_knowledge", arguments=json.dumps(arguments, ensure_ascii=False)))


def test_registration_schema_hides_internal_retrieve():
    _, tools = lesson.build_registration(Mock())
    schema = tools[0]["function"]
    assert schema["name"] == "search_knowledge"
    params = schema["parameters"]
    assert set(params["properties"]) == {"query", "top_k"}
    assert params["required"] == ["query"]
    assert params["additionalProperties"] is False
    assert params["properties"]["top_k"]["default"] == 3


@pytest.mark.parametrize("args", [
    {}, {"query": "  "}, {"query": 123}, {"query": "问", "top_k": 0},
    {"query": "问", "top_k": 6}, {"query": "问", "top_k": True},
    {"query": "问", "top_k": "3"}, {"query": "问", "retrieve": "伪造函数"},
])
def test_invalid_arguments_never_retrieve(monkeypatch, args):
    retrieve = Mock(side_effect=AssertionError("无效参数不应检索"))
    install_for_test(monkeypatch, retrieve)
    result = agent.execute_tool_call(make_call(args))
    assert result["success"] is False
    assert result["error_type"] == "validation_error"
    retrieve.assert_not_called()


def test_exercise_packages_sources_without_vectors_or_mutation():
    hits = make_hits()
    before = deepcopy(hits)
    retrieve = Mock(return_value=hits)
    result = lesson.search_knowledge("住在哪里？", 2, retrieve)
    retrieve.assert_called_once_with("住在哪里？", 2)
    assert result == {
        "success": True, "query": "住在哪里？", "source_count": 2,
        "sources": [{"chunk_id": "demo_000", "text": "练习角色住在示例地区。"},
                    {"chunk_id": "demo_001", "text": "当地有图书馆。"}],
    }
    assert hits == before
    assert "embedding" not in json.dumps(result)


def test_exercise_empty_search_is_not_execution_failure():
    retrieve = Mock(return_value=[])
    result = lesson.search_knowledge("找不到的内容", 3, retrieve)
    assert result == {"success": True, "query": "找不到的内容", "sources": [], "source_count": 0}


def test_exercise_default_k_and_strip_are_applied_by_executor(monkeypatch):
    retrieve = Mock(return_value=make_hits())
    install_for_test(monkeypatch, retrieve)
    result = agent.execute_tool_call(make_call({"query": "  住在哪里？  "}))
    retrieve.assert_called_once_with("住在哪里？", 3)
    assert result["source_count"] == 2


def test_exercise_real_agent_loop_gets_tool_evidence(monkeypatch):
    retrieve = Mock(return_value=make_hits()[:1])
    install_for_test(monkeypatch, retrieve)
    tool_call = make_call({"query": "练习角色住在哪里？", "top_k": 1})
    expected_answer = "根据学习资料，练习角色住在示例地区。[demo_000]"
    replies = [
        SimpleNamespace(role="assistant", content=None, tool_calls=[tool_call]),
        SimpleNamespace(role="assistant", content=expected_answer, tool_calls=None),
    ]
    requests = []

    def fake_create(**kwargs):
        requests.append(deepcopy(kwargs))
        assert replies, "不应发起第三次模型请求"
        return SimpleNamespace(choices=[SimpleNamespace(message=replies.pop(0))])

    fake_llm = SimpleNamespace(model="fake-model", temperature=0, client=SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))))
    monkeypatch.setattr(agent, "LLMClient", lambda: fake_llm)
    assert agent.ask_agent("练习角色住在哪里？", max_tool_rounds=2) == expected_answer
    retrieve.assert_called_once_with("练习角色住在哪里？", 1)
    assert len(requests) == 2
    assert len(requests[0]["messages"]) == 2
    assert requests[0]["tools"][0]["function"]["name"] == "search_knowledge"
    second_messages = requests[1]["messages"]
    assert len(second_messages) == 4
    assert second_messages[2].tool_calls[0].id == "call_search_001"
    tool_message = second_messages[3]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call_search_001"
    result = json.loads(tool_message["content"])
    assert result["sources"] == [{"chunk_id": "demo_000", "text": "练习角色住在示例地区。"}]
    # 这证明资料被送到第二次模型请求，不证明真实模型一定遵循资料作答。
