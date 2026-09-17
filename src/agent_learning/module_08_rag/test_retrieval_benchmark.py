"""不请求真实模型；检索函数作为替身注入，指标计算使用真实实现。"""

from copy import deepcopy
from unittest.mock import Mock, call

import pytest

from agent_learning.module_08_rag import retrieval_benchmark as lesson


def sample_cases():
    return [
        {"case_id": "q1", "query": "问题一", "expected_chunk_ids": ["A", "B"]},
        {"case_id": "q2", "query": "问题二", "expected_chunk_ids": ["C"]},
    ]


def test_exercise_preserves_rank_labels_and_input():
    cases = sample_cases()
    original = deepcopy(cases)
    retrieve = Mock(side_effect=[
        [{"chunk": {"chunk_id": "X"}}, {"chunk": {"chunk_id": "A"}}], [],
    ])
    results = lesson.collect_retrieval_results(cases, retrieve, k=2)
    assert retrieve.call_args_list == [call("问题一", 2), call("问题二", 2)]
    assert results == [{**cases[0], "retrieved_chunk_ids": ["X", "A"]},
                       {**cases[1], "retrieved_chunk_ids": []}]
    assert results[0] is not cases[0]
    assert cases == original
    report = lesson.evaluate_cases(results, k=2)
    assert report["hit_rate_at_k"] == pytest.approx(0.5)
    assert report["mean_recall_at_k"] == pytest.approx(0.25)


def test_exercise_retrieval_error_propagates():
    retrieve = Mock(side_effect=RuntimeError("测试检索失败"))
    with pytest.raises(RuntimeError, match="测试检索失败"):
        lesson.collect_retrieval_results(sample_cases(), retrieve)
    retrieve.assert_called_once_with("问题一", 3)


def test_bad_later_case_fails_before_any_retrieval():
    cases = sample_cases()
    cases[1]["expected_chunk_ids"] = []
    retrieve = Mock()
    with pytest.raises(ValueError, match="预期片段"):
        lesson.collect_retrieval_results(cases, retrieve)
    retrieve.assert_not_called()


@pytest.mark.parametrize("k", [0, True, 1.5])
def test_bad_k(k):
    with pytest.raises(ValueError, match="k 必须"):
        lesson.collect_retrieval_results(sample_cases(), Mock(), k)


def test_empty_cases():
    with pytest.raises(ValueError, match="cases 不能为空"):
        lesson.collect_retrieval_results([], Mock())


def test_current_labels_match_local_corpus():
    chunks = lesson.build_overlapping_chunks(lesson.load_documents(), 300, 50)
    lesson.validate_benchmark(chunks)


def test_changed_corpus_is_rejected():
    with pytest.raises(ValueError, match="重新核对"):
        lesson.validate_benchmark([])


def test_default_is_offline(monkeypatch, capsys):
    create_client = Mock(side_effect=AssertionError("默认运行不创建客户端"))
    monkeypatch.setattr(lesson, "create_embedding_client", create_client)
    monkeypatch.setattr("sys.argv", ["lesson"])
    lesson.main()
    assert "3 个标注问题" in capsys.readouterr().out
    create_client.assert_not_called()
