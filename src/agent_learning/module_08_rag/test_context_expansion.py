"""相邻扩展、跨命中去重、来源编号的离线练习。"""

from copy import deepcopy

import pytest

from agent_learning.module_08_rag.context_expansion import expand_context_chunks, make_example
from agent_learning.module_08_rag.rag_answering import build_rag_messages


def ids(chunks):
    return [chunk["chunk_id"] for chunk in chunks]


def test_exercise_expands_deduplicates_and_keeps_full_chunks():
    chunks, hits = make_example()
    original = deepcopy((chunks, hits))
    selected = expand_context_chunks(chunks, hits, 1)
    assert ids(selected) == ["A_000", "A_001", "A_002", "A_003"]
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    assert selected == [by_id[cid] for cid in ids(selected)]
    assert (chunks, hits) == original
    assert all("score" not in chunk for chunk in selected)


def test_exercise_zero_window_and_repeated_hit():
    chunks, hits = make_example()
    assert ids(expand_context_chunks(chunks, hits + hits, 0)) == ["A_001", "A_002"]


def test_exercise_first_seen_order_and_separate_documents():
    chunks, hits = make_example()
    b_chunk = next(chunk for chunk in chunks if chunk["document_id"] == "B")
    reordered = [hits[1], {"chunk": b_chunk}, hits[0]]
    assert ids(expand_context_chunks(chunks, reordered, 1)) == [
        "A_001", "A_002", "A_003", "B_001", "A_000",
    ]


def test_exercise_missing_id_is_not_silently_skipped():
    chunks, _ = make_example()
    with pytest.raises(ValueError, match="找不到命中片段"):
        expand_context_chunks(chunks, [{"chunk": {"chunk_id": "missing"}}])


def test_exercise_message_uses_final_source_numbers():
    chunks, hits = make_example()
    selected = expand_context_chunks(chunks, hits)
    context_hits = [{"chunk": chunk} for chunk in selected]
    content = build_rag_messages("原因是什么？", context_hits)[1]["content"]
    for number, chunk in enumerate(selected, start=1):
        assert content.count(f"[{number}] 片段编号：{chunk['chunk_id']}") == 1
        assert chunk["text"] in content
    assert "[5]" not in content


def test_no_hits():
    chunks, _ = make_example()
    assert expand_context_chunks(chunks, []) == []


@pytest.mark.parametrize("window", [-1, True, 0.5])
def test_bad_window(window):
    chunks, hits = make_example()
    with pytest.raises(ValueError, match="window 必须"):
        expand_context_chunks(chunks, hits, window)


def test_duplicate_corpus_id():
    chunks, hits = make_example()
    with pytest.raises(ValueError, match="必须唯一"):
        expand_context_chunks(chunks + [chunks[0]], hits)
