"""只用替身测真实接口适配层，不读密钥、不联网。"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent_learning.module_08_rag import rag_live_acceptance as lesson
from agent_learning.module_08_rag.context_expansion import make_example


def fake_llm(content="根据学习资料，答案。[1]", finish_reason="stop"):
    response = SimpleNamespace(
        model="fake-model", usage=Mock(model_dump=Mock(return_value={"total_tokens": 42})),
        choices=[SimpleNamespace(finish_reason=finish_reason,
                                 message=SimpleNamespace(content=content))],
    )
    client = Mock()
    client.with_options.return_value.chat.completions.create.return_value = response
    return SimpleNamespace(client=client, model="fake-model", temperature=0.5)


def test_generate_sends_exact_messages_once_and_records_usage():
    llm, audit = fake_llm(), []
    generate = lesson.make_generate(llm, audit)
    messages = [{"role": "user", "content": "问题和资料"}]
    assert generate(messages) == "根据学习资料，答案。[1]"
    llm.client.with_options.assert_called_once_with(timeout=20.0, max_retries=0)
    llm.client.with_options.return_value.chat.completions.create.assert_called_once_with(
        model="fake-model", messages=messages, temperature=0.5,
        max_tokens=1024, extra_body={"thinking": {"type": "disabled"}},
    )
    assert audit[0]["usage"] == {"total_tokens": 42}
    assert audit[0]["status"] == "completed"


@pytest.mark.parametrize("content,reason", [("部分回答", "length"), (None, "stop"), ("  ", "stop")])
def test_bad_response_stops_without_retry(content, reason):
    llm, audit = fake_llm(content, reason), []
    with pytest.raises(RuntimeError):
        lesson.make_generate(llm, audit)([])
    assert llm.client.with_options.return_value.chat.completions.create.call_count == 1
    assert audit[0]["status"] == "responded"


def test_retrieve_only_embeds_query_and_uses_saved_vectors(monkeypatch):
    embed = Mock(return_value=[1.0, 0.0])
    monkeypatch.setattr(lesson, "embed_text", embed)
    client, audit = object(), []
    index = [{"chunk_id": "A", "embedding": [1.0, 0.0]},
             {"chunk_id": "B", "embedding": [0.0, 1.0]}]
    hits = lesson.make_retrieve(client, "fake-embedding", index, audit)("问题", 1)
    embed.assert_called_once_with(client, "fake-embedding", "问题")
    assert [hit["chunk"]["chunk_id"] for hit in hits] == ["A"]
    assert audit[0]["dimension"] == 2


def test_three_cases_call_each_callback_three_times():
    chunks, hits = make_example()
    retrieve, generate = Mock(return_value=hits), Mock(return_value="答案。[1]")
    reports = list(lesson.run_cases(chunks, retrieve, generate))
    assert len(reports) == retrieve.call_count == generate.call_count == 3
    assert all(report["input_unit"] == "characters_not_tokens" for report in reports)
    for report, call in zip(reports, generate.call_args_list):
        assert call.args[0] == report["messages"]
        assert report["input_size"] <= 6000


def test_failure_stops_remaining_cases():
    chunks, hits = make_example()
    retrieve, generate = Mock(return_value=hits), Mock(side_effect=RuntimeError("超时"))
    with pytest.raises(RuntimeError, match="超时"):
        list(lesson.run_cases(chunks, retrieve, generate))
    assert retrieve.call_count == generate.call_count == 1


def test_default_main_does_not_create_client(monkeypatch, capsys):
    factory = Mock(side_effect=AssertionError("不应创建真实客户端"))
    monkeypatch.setattr(lesson, "create_embedding_client", factory)
    monkeypatch.setattr("sys.argv", ["rag_live_acceptance"])
    lesson.main()
    factory.assert_not_called()
    assert "--live" in capsys.readouterr().out


def test_missing_cache_fails_before_creating_client(monkeypatch, tmp_path):
    factory = Mock(side_effect=AssertionError("不应创建客户端"))
    monkeypatch.setattr(lesson, "create_embedding_client", factory)
    monkeypatch.setattr("sys.argv", ["rag_live_acceptance", "--live", "--index-file",
                                     str(tmp_path / "missing.json")])
    with pytest.raises(FileNotFoundError):
        lesson.main()
    factory.assert_not_called()


def test_invalid_cache_stops_before_api_and_closes_client(monkeypatch):
    client = Mock()
    monkeypatch.setattr("sys.argv", ["rag_live_acceptance", "--live"])
    monkeypatch.setattr(lesson, "load_index", Mock(return_value={"version": 999}))
    monkeypatch.setattr(lesson, "load_documents", Mock(return_value=[]))
    monkeypatch.setattr(lesson, "create_embedding_client", Mock(return_value=(client, "fake")))
    with pytest.raises(ValueError, match="索引格式"):
        lesson.main()
    client.embeddings.create.assert_not_called()
    client.close.assert_called_once_with()


def test_chat_exception_records_attempt_without_retry():
    llm, audit = fake_llm(), []
    call = llm.client.with_options.return_value.chat.completions.create
    call.side_effect = RuntimeError("服务暂不可用")
    with pytest.raises(RuntimeError, match="服务暂不可用"):
        lesson.make_generate(llm, audit)([])
    call.assert_called_once()
    assert audit == [{"kind": "chat", "status": "started"}]
