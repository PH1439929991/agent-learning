"""真实验收入口的离线护栏测试：不创建真实客户端、不联网。"""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletion

from agent_learning.module_08_rag import rag_agent_live as lesson


def response(tool=False, *, name="search_knowledge", arguments=None, count=1,
             finish=None, content="根据学习资料，旅伴是皮克斯。[lulu_000]"):
    message = {"role": "assistant", "content": None if tool else content}
    if tool:
        message["tool_calls"] = [
            {"id": f"call_{i}", "type": "function", "function": {
                "name": name, "arguments": arguments if arguments is not None
                else json.dumps({"query": "璐璐的旅伴", "top_k": 1})}}
            for i in range(count)
        ]
    return ChatCompletion.model_validate({
        "id": "fake", "created": 0, "model": "fake-model", "object": "chat.completion",
        "choices": [{"index": 0, "message": message,
                     "finish_reason": finish or ("tool_calls" if tool else "stop")}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    })


def setup(replies):
    requests = []
    def create(**kwargs):
        requests.append(deepcopy(kwargs))
        if not replies:
            pytest.fail("不允许多发请求")
        return replies.pop(0)
    client = Mock()
    client.with_options.return_value.chat.completions.create.side_effect = create
    llm = SimpleNamespace(client=client, model="fake-model", temperature=0.5)
    retrieve = Mock(return_value=[{"chunk": {"chunk_id": "lulu_000", "text": "旅伴是皮克斯。"}, "score": 0.9}])
    return llm, retrieve, requests


def test_two_requests_include_call_and_evidence():
    llm, retrieve, requests = setup([response(True), response()])
    audit = []
    result = lesson.run_agent_once("璐璐的旅伴是谁？", llm, retrieve, audit)
    assert result["status"] == "answered_after_tool"
    assert result["tool_result"]["sources"][0]["chunk_id"] == "lulu_000"
    retrieve.assert_called_once_with("璐璐的旅伴", 1)
    assert len(requests) == 2
    assert [r["tool_choice"] for r in requests] == ["auto", "none"]
    assert len(requests[0]["messages"]) == 2
    second = requests[1]["messages"]
    assert [m["role"] for m in second] == ["system", "user", "assistant", "tool"]
    assert second[3]["tool_call_id"] == second[2]["tool_calls"][0]["id"]
    assert json.loads(second[3]["content"]) == result["tool_result"]
    llm.client.with_options.assert_called_once_with(timeout=20.0, max_retries=0)
    assert all(r["max_tokens"] == 1024 for r in requests)
    assert all(r["extra_body"]["thinking"]["type"] == "disabled" for r in requests)
    assert [e["usage"]["total_tokens"] for e in audit] == [15, 15]


def test_direct_answer_does_not_retrieve_or_claim_tool_used():
    llm, retrieve, requests = setup([response(content="你好")])
    result = lesson.run_agent_once("你好", llm, retrieve, [])
    assert result["status"] == "direct_answer"
    assert result["tool_result"] is None
    assert len(requests) == 1
    retrieve.assert_not_called()


@pytest.mark.parametrize("first", [response(True, count=2), response(True, name="unknown"),
    response(True, arguments="{"), response(True, arguments='{"query":"  "}'),
    response(True, arguments='{"query":"问题","top_k":6}'), response(finish="length")])
def test_bad_first_reply_never_retrieves(first):
    llm, retrieve, requests = setup([first])
    with pytest.raises((ValueError, RuntimeError)):
        lesson.run_agent_once("问题", llm, retrieve, [])
    assert len(requests) == 1
    retrieve.assert_not_called()


@pytest.mark.parametrize("final", [response(True), response(finish="length"), response(content=" ")])
def test_bad_final_stops_without_third_request(final):
    llm, retrieve, requests = setup([response(True), final])
    with pytest.raises(RuntimeError):
        lesson.run_agent_once("问题", llm, retrieve, [])
    assert len(requests) == 2
    assert retrieve.call_count == 1


def test_tool_failure_stops_before_second_chat():
    llm, retrieve, requests = setup([response(True)])
    retrieve.side_effect = RuntimeError("测试服务异常")
    with pytest.raises(RuntimeError, match="测试服务异常"):
        lesson.run_agent_once("问题", llm, retrieve, [])
    assert len(requests) == 1
    assert retrieve.call_count == 1


def test_large_tool_result_stops_before_second_chat():
    llm, retrieve, requests = setup([response(True)])
    retrieve.return_value[0]["chunk"]["text"] = "长" * 12000
    with pytest.raises(ValueError, match="字符护栏"):
        lesson.run_agent_once("问题", llm, retrieve, [])
    assert len(requests) == 1


def test_default_entry_does_not_create_clients(monkeypatch):
    factory = Mock(side_effect=AssertionError("不能创建客户端"))
    monkeypatch.setattr(lesson, "create_embedding_client", factory)
    monkeypatch.setattr("sys.argv", ["rag_agent_live"])
    lesson.main()
    factory.assert_not_called()
