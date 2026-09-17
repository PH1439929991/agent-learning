"""第十四节离线测试：计算真实指标，但不请求模型。"""

from copy import deepcopy
from unittest.mock import Mock, call

import pytest

from agent_learning.module_08_rag.retrieval_k_comparison import compare_top_k


def sample():
    return [{"case_id": "q1", "query": "问题一", "expected_chunk_ids": ["A", "B"]},
            {"case_id": "q2", "query": "问题二", "expected_chunk_ids": ["C"]}]


def test_exercise_reuses_rankings_and_keeps_details():
    cases, ks = sample(), [3, 1, 2, 3]
    before = deepcopy((cases, ks))
    retrieve = Mock(side_effect=[
        [{"chunk": {"chunk_id": x}} for x in ["X", "A", "B"]],
        [{"chunk": {"chunk_id": x}} for x in ["C", "X", "A"]],
    ])
    reports = compare_top_k(cases, retrieve, ks)
    assert retrieve.call_args_list == [call("问题一", 3), call("问题二", 3)]
    assert [r["k"] for r in reports] == [1, 2, 3]
    assert [r["hit_rate_at_k"] for r in reports] == pytest.approx([0.5, 1, 1])
    assert [r["mean_recall_at_k"] for r in reports] == pytest.approx([0.5, 0.75, 1])
    for report in reports:
        assert report["case_count"] == 2
        assert [row["case_id"] for row in report["details"]] == ["q1", "q2"]
    assert reports[0]["details"][0]["matched_ids"] == []
    assert reports[2]["details"][0]["matched_ids"] == ["A", "B"]
    assert (cases, ks) == before


def test_exercise_empty_retrieval_is_scored():
    retrieve = Mock(return_value=[])
    reports = compare_top_k(sample(), retrieve, [1, 5])
    assert retrieve.call_count == 2
    assert [r["mean_recall_at_k"] for r in reports] == [0, 0]
    assert [r["hit_rate_at_k"] for r in reports] == [0, 0]


def test_exercise_invalid_case_fails_before_retrieving():
    cases = sample()
    cases[1]["expected_chunk_ids"] = []
    retrieve = Mock()
    with pytest.raises(ValueError, match="预期片段"):
        compare_top_k(cases, retrieve, [1, 3])
    retrieve.assert_not_called()


@pytest.mark.parametrize("ks", [[0], [True], [1.5], []])
def test_bad_ks(ks):
    retrieve = Mock()
    with pytest.raises(ValueError, match="ks 必须"):
        compare_top_k(sample(), retrieve, ks)
    retrieve.assert_not_called()


def test_empty_cases():
    retrieve = Mock()
    with pytest.raises(ValueError, match="cases 不能为空"):
        compare_top_k([], retrieve, [1])
    retrieve.assert_not_called()
