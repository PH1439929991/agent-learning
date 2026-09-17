"""上下文选择的离线测试；不使用真实 tokenizer 或模型接口。"""

from copy import deepcopy

import pytest

from agent_learning.module_08_rag import context_budget as lesson


def size(query, chunks):
    return lesson.demo_character_count(lesson.messages_for_chunks(query, chunks))


def test_exercise_skips_large_chunk_and_renumbers():
    query, chunks = lesson.make_example()
    before = deepcopy(chunks)
    budget = size(query, [chunks[0], chunks[2]])
    result = lesson.select_context(query, chunks, budget, lesson.demo_character_count)
    assert result["selected_chunks"] == [chunks[0], chunks[2]]
    assert result["omitted_chunks"] == [chunks[1]]
    assert result["input_size"] == budget
    assert result["input_budget"] == budget
    assert result["source_count"] == 2
    assert result["messages"] == lesson.messages_for_chunks(query, [chunks[0], chunks[2]])
    content = result["messages"][1]["content"]
    assert "[1] 片段编号：A" in content
    assert "[2] 片段编号：C" in content
    assert "[3]" not in content
    assert chunks == before


def test_exercise_all_fit_including_exact_boundary():
    query, chunks = lesson.make_example()
    budget = size(query, chunks)
    result = lesson.select_context(query, chunks, budget, lesson.demo_character_count)
    assert result["selected_chunks"] == chunks
    assert result["omitted_chunks"] == []
    assert result["input_size"] == budget


@pytest.mark.parametrize("empty", [False, True])
def test_exercise_no_evidence_fits_or_no_candidates(empty):
    query, chunks = lesson.make_example()
    candidates = [] if empty else chunks
    budget = size(query, [])
    result = lesson.select_context(query, candidates, budget, lesson.demo_character_count)
    assert result["selected_chunks"] == []
    assert result["omitted_chunks"] == candidates
    assert result["source_count"] == 0
    assert result["messages"] == lesson.messages_for_chunks(query, [])
    assert result["input_size"] == budget


def test_exercise_uses_supplied_counter():
    query, chunks = lesson.make_example()
    # 换一种演示单位，不允许实现里偷偷写死 len 或固定换算系数。
    def double_count(messages):
        return 2 * lesson.demo_character_count(messages)
    budget = 2 * size(query, [chunks[0]])
    result = lesson.select_context(query, chunks, budget, double_count)
    assert result["selected_chunks"] == [chunks[0]]
    assert result["input_size"] == budget


def test_baseline_over_budget():
    query, _ = lesson.make_example()
    with pytest.raises(ValueError, match="基础消息"):
        lesson.select_context(query, [], size(query, []) - 1, lesson.demo_character_count)


@pytest.mark.parametrize("budget", [-1, True, 2.5])
def test_bad_budget(budget):
    with pytest.raises(ValueError, match="input_budget"):
        lesson.select_context("问题", [], budget, lesson.demo_character_count)


def test_duplicate_ids():
    query, chunks = lesson.make_example()
    with pytest.raises(ValueError, match="去重"):
        lesson.select_context(query, chunks + chunks, 10000, lesson.demo_character_count)


def test_bad_counter():
    with pytest.raises(ValueError, match="计数函数"):
        lesson.select_context("问题", [], 10000, lambda messages: -1)


def test_blank_question():
    with pytest.raises(ValueError, match="query 不能为空"):
        lesson.select_context("  ", [], 10000, lesson.demo_character_count)
