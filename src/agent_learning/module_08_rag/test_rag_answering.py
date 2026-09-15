"""第八节离线测试：不请求模型；exercise 用例需要先完成 TODO。"""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from agent_learning.module_08_rag import rag_answering as lesson


def two_hits():
    hits = lesson.demo_hits()
    second = deepcopy(hits[0])
    second["chunk"]["chunk_id"] = "demo_001"
    second["chunk"]["text"] = "第二段：练习角色喜欢阅读。"
    hits.append(second)
    return hits


def test_exercise_roles_question_and_sources():
    hits = two_hits()
    messages = lesson.build_rag_messages("角色喜欢什么？", hits)
    assert len(messages) == 2
    assert messages[0] == {"role": "system", "content": lesson.SYSTEM_PROMPT}
    assert messages[1]["role"] == "user"
    content = messages[1]["content"]
    assert "角色喜欢什么？" in content
    assert lesson.format_chunk(hits[0], 1) in content
    assert lesson.format_chunk(hits[1], 2) in content
    assert content.index("[1]") < content.index("[2]")


def test_exercise_no_vectors_scores_or_mutation():
    hits = two_hits()
    original = deepcopy(hits)
    messages = lesson.build_rag_messages("问题", hits)
    content = messages[1]["content"]
    assert "embedding" not in content
    assert "score" not in content
    assert "[0.6, 0.8]" not in content
    assert hits == original


def test_exercise_empty_context():
    messages = lesson.build_rag_messages("问题", [])
    assert "（没有检索到资料）" in messages[1]["content"]


def test_exercise_calls_generator_with_messages():
    hits = two_hits()
    generate = Mock(return_value="根据学习资料，角色喜欢阅读。[2]")
    answer = lesson.answer_from_hits("角色喜欢什么？", hits, generate)
    generate.assert_called_once_with(lesson.build_rag_messages("角色喜欢什么？", hits))
    assert answer == "根据学习资料，角色喜欢阅读。[2]"


def test_exercise_demo(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["lesson", "--demo"])
    create_client = Mock(side_effect=AssertionError("离线演示不能创建真实客户端"))
    monkeypatch.setattr(lesson, "create_embedding_client", create_client)
    lesson.main()
    assert "demo_000" in capsys.readouterr().out
    create_client.assert_not_called()


def test_no_hits_does_not_generate():
    generate = Mock()
    assert lesson.answer_from_hits("问题", [], generate) == lesson.NO_EVIDENCE_ANSWER
    generate.assert_not_called()


def test_blank_query():
    with pytest.raises(ValueError, match="query 不能为空"):
        lesson.build_rag_messages("  ", [])
    generate = Mock()
    with pytest.raises(ValueError, match="query 不能为空"):
        lesson.answer_from_hits("  ", [], generate)
    generate.assert_not_called()


def test_format_chunk():
    content = lesson.format_chunk(lesson.demo_hits()[0], 1)
    assert "[1] 片段编号：demo_000" in content
    assert "正文：这是演示资料" in content
    assert "未标注" in content
    assert "embedding" not in content


def test_generation_error_propagates(monkeypatch):
    monkeypatch.setattr(lesson, "build_rag_messages", Mock(return_value=[]))
    generate = Mock(side_effect=RuntimeError("测试生成失败"))
    with pytest.raises(RuntimeError, match="测试生成失败"):
        lesson.answer_from_hits("问题", lesson.demo_hits(), generate)
    generate.assert_called_once()


def test_default_does_not_create_client(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["lesson"])
    create_client = Mock(side_effect=AssertionError("默认运行不能创建真实客户端"))
    monkeypatch.setattr(lesson, "create_embedding_client", create_client)
    lesson.main()
    assert "三个 TODO" in capsys.readouterr().out
    create_client.assert_not_called()
