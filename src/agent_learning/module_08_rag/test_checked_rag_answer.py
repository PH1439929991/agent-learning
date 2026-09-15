"""第十节：生成器是假函数，消息组装与编号检查使用真实实现。"""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from agent_learning.module_08_rag.checked_rag_answer import answer_with_citation_check
from agent_learning.module_08_rag.rag_answering import (
    NO_EVIDENCE_ANSWER, build_rag_messages, demo_hits,
)


@pytest.mark.parametrize("number,invalid,valid", [(1, [], True), (2, [2], False)])
def test_answer_and_citation_report(number, invalid, valid):
    hits = demo_hits()  # 实际只有一段资料，只有 [1] 有效。
    original = deepcopy(hits)
    answer = f"根据学习资料，练习角色居住在示例地区。[{number}]"
    generate = Mock(return_value=answer)

    result = answer_with_citation_check("住在哪里？", hits, generate)

    # 校验失败也保留原回答，不修饰、不删除错误编号、不重新生成。
    assert result == {
        "answer": answer,
        "citation_check": {
            "cited_numbers": [number], "invalid_numbers": invalid,
            "has_citations": True, "references_valid": valid,
        },
    }
    generate.assert_called_once_with(build_rag_messages("住在哪里？", hits))
    assert hits == original


def test_no_hits_skips_generation():
    generate = Mock(side_effect=AssertionError("没有资料时不应调用生成器"))
    result = answer_with_citation_check("问题", [], generate)
    assert result["answer"] == NO_EVIDENCE_ANSWER
    assert result["citation_check"] == {
        "cited_numbers": [], "invalid_numbers": [],
        "has_citations": False, "references_valid": False,
    }
    generate.assert_not_called()


def test_answer_without_citation_is_preserved():
    generate = Mock(return_value="资料不足，无法回答。")
    result = answer_with_citation_check("问题", demo_hits(), generate)
    assert result["answer"] == "资料不足，无法回答。"
    assert result["citation_check"]["has_citations"] is False
    assert result["citation_check"]["references_valid"] is False
    generate.assert_called_once()


def test_generation_error_is_not_hidden_or_retried():
    generate = Mock(side_effect=RuntimeError("测试生成失败"))
    with pytest.raises(RuntimeError, match="测试生成失败"):
        answer_with_citation_check("问题", demo_hits(), generate)
    generate.assert_called_once()


def test_blank_query_does_not_generate():
    generate = Mock()
    with pytest.raises(ValueError, match="query 不能为空"):
        answer_with_citation_check("  ", demo_hits(), generate)
    generate.assert_not_called()
