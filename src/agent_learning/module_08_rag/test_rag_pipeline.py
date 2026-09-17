"""第十七节综合题：仅外部检索、生成用替身，其余执行真实代码。"""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from agent_learning.module_08_rag import rag_pipeline as lesson
from agent_learning.module_08_rag.context_budget import messages_for_chunks


def test_exercise_full_pipeline():
    chunks, hits = lesson.make_example()
    before = deepcopy((chunks, hits))
    retrieve = Mock(return_value=hits[:1])
    generate = Mock(return_value="根据学习资料，因为那里有图书馆。[3]")
    result = lesson.run_rag("为什么？", chunks, retrieve, generate, 2000,
                            lesson.demo_character_count, top_k=1)
    retrieve.assert_called_once_with("为什么？", 1)
    generate.assert_called_once_with(result["messages"])
    assert result["status"] == "generated"
    assert result["retrieved_ids"] == ["A_001"]
    assert result["source_ids"] == ["A_001", "A_000", "A_002"]
    assert result["source_count"] == 3
    assert result["input_size"] == lesson.demo_character_count(result["messages"])
    assert result["input_size"] <= 2000
    assert result["citation_check"]["references_valid"] is True
    assert (chunks, hits) == before


def test_exercise_budget_applies_before_generation_and_citation_check():
    chunks, hits = lesson.make_example()
    query = "问题"
    budget = lesson.demo_character_count(messages_for_chunks(query, [hits[0]["chunk"]]))
    retrieve = Mock(return_value=hits[:1])
    generate = Mock(return_value="故意使用越界引用。[2]")
    result = lesson.run_rag(query, chunks, retrieve, generate, budget, lesson.demo_character_count)
    assert result["source_ids"] == ["A_001"]
    assert result["omitted_ids"] == ["A_000", "A_002"]
    assert result["input_size"] == budget
    assert result["source_count"] == 1
    assert result["citation_check"]["invalid_numbers"] == [2]
    assert result["answer"] == "故意使用越界引用。[2]"
    generate.assert_called_once_with(result["messages"])


@pytest.mark.parametrize("empty_hits,expected_status", [(True, "no_retrieval"), (False, "no_context")])
def test_exercise_no_usable_context_skips_generation(empty_hits, expected_status):
    chunks, hits = lesson.make_example()
    budget = lesson.demo_character_count(messages_for_chunks("问题", []))
    retrieve = Mock(return_value=[] if empty_hits else hits)
    generate = Mock(side_effect=AssertionError("没有片段不能生成"))
    result = lesson.run_rag("问题", chunks, retrieve, generate, budget, lesson.demo_character_count)
    assert result["status"] == expected_status
    assert result["source_count"] == 0
    assert result["source_ids"] == []
    assert result["citation_check"]["has_citations"] is False
    generate.assert_not_called()


def test_exercise_generation_error_is_not_hidden():
    chunks, hits = lesson.make_example()
    generate = Mock(side_effect=RuntimeError("测试生成失败"))
    with pytest.raises(RuntimeError, match="测试生成失败"):
        lesson.run_rag("问题", chunks, Mock(return_value=hits), generate, 2000,
                       lesson.demo_character_count)
    generate.assert_called_once()


def test_exercise_unknown_hit_stops_before_generation():
    chunks, _ = lesson.make_example()
    generate = Mock()
    with pytest.raises(ValueError, match="找不到命中片段"):
        lesson.run_rag("问题", chunks, Mock(return_value=[{"chunk": {"chunk_id": "unknown"}}]),
                       generate, 2000, lesson.demo_character_count)
    generate.assert_not_called()


def test_priority_helper():
    chunks, hits = lesson.make_example()
    expanded = lesson.expand_context_chunks(chunks, hits)
    assert [c["chunk_id"] for c in lesson.prioritize_hits(hits, expanded)] == [
        "A_001", "A_002", "A_000", "A_003",
    ]


def test_invalid_budget_stops_before_retrieval():
    retrieve, generate = Mock(), Mock()
    with pytest.raises(ValueError, match="基础消息"):
        lesson.run_rag("问题", [], retrieve, generate, 0, lesson.demo_character_count)
    retrieve.assert_not_called()
    generate.assert_not_called()


@pytest.mark.parametrize("kwargs", [{"top_k": 0}, {"window": -1}])
def test_invalid_options(kwargs):
    retrieve = Mock()
    with pytest.raises(ValueError):
        lesson.run_rag("问题", [], retrieve, Mock(), 2000, lesson.demo_character_count, **kwargs)
    retrieve.assert_not_called()
