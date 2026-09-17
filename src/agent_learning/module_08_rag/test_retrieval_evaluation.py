"""单题实现回归与多题汇总练习，全部离线。"""

from copy import deepcopy

import pytest

from agent_learning.module_08_rag.retrieval_evaluation import (
    demo_cases, evaluate_cases, evaluate_retrieval,
)


def test_exercise_summary_and_details():
    cases = demo_cases()
    original = deepcopy(cases)
    report = evaluate_cases(cases, k=3)
    assert set(report) == {"k", "case_count", "hit_rate_at_k", "mean_recall_at_k", "details"}
    assert report["k"] == 3
    assert report["case_count"] == 3
    assert report["hit_rate_at_k"] == pytest.approx(2 / 3)
    assert report["mean_recall_at_k"] == pytest.approx(0.5)
    assert report["details"] == [
        {"case_id": case["case_id"], "query": case["query"],
         **evaluate_retrieval(case["expected_chunk_ids"], case["retrieved_chunk_ids"], 3)}
        for case in cases
    ]
    assert cases == original


def test_exercise_k_is_forwarded():
    report = evaluate_cases(demo_cases(), k=1)
    assert report["hit_rate_at_k"] == pytest.approx(1 / 3)
    assert report["mean_recall_at_k"] == pytest.approx(1 / 3)


def test_exercise_every_question_has_equal_weight():
    cases = [
        {"case_id": "one", "query": "问题一", "expected_chunk_ids": ["A"],
         "retrieved_chunk_ids": ["A"]},
        {"case_id": "two", "query": "问题二", "expected_chunk_ids": ["B", "C", "D"],
         "retrieved_chunk_ids": ["X"]},
    ]
    report = evaluate_cases(cases)
    # 平均单题召回率为 (1+0)/2，不是把片段合并后计算的 1/4。
    assert report["mean_recall_at_k"] == pytest.approx(0.5)
    assert report["hit_rate_at_k"] == pytest.approx(0.5)


def test_exercise_invalid_question_is_not_skipped():
    cases = demo_cases()
    cases[1]["expected_chunk_ids"] = []
    with pytest.raises(ValueError, match="预期相关片段"):
        evaluate_cases(cases)


def test_single_question_duplicates():
    assert evaluate_retrieval(["A", "A", "B"], ["A", "A", "B"], 2) == {
        "hit_at_k": True, "recall_at_k": 0.5, "matched_ids": ["A"],
    }


def test_single_question_no_results():
    assert evaluate_retrieval(["A"], [], 3) == {
        "hit_at_k": False, "recall_at_k": 0.0, "matched_ids": [],
    }


@pytest.mark.parametrize("k", [0, True, 1.5])
def test_invalid_k(k):
    with pytest.raises(ValueError, match="k 必须"):
        evaluate_cases(demo_cases(), k)


def test_empty_cases():
    with pytest.raises(ValueError, match="cases 不能为空"):
        evaluate_cases([])
