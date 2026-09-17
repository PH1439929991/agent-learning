"""第十二节：汇总多道题的检索指标。纯离线，不调用模型。

evaluate_retrieval 沿用你在第十一节完成的实现。
只填写 evaluate_cases 的三个 TODO；示例排名是手写数据，不是真实检索表现。
"""

import json


def evaluate_retrieval(
    expected_chunk_ids: list[str],
    retrieved_chunk_ids: list[str],
    k: int = 3,
) -> dict:
    """已完成：单题评测，先截取前 K 条，再去重计数。"""
    if type(k) is not int or k < 1:
        raise ValueError("k 必须是正整数")
    if not expected_chunk_ids:
        raise ValueError("本题需要至少一个预期相关片段")
    expected = set(expected_chunk_ids)
    retrieved = set(retrieved_chunk_ids[:k])
    matched = expected & retrieved
    return {
        "hit_at_k": bool(matched),
        "recall_at_k": len(matched) / len(expected),
        "matched_ids": sorted(matched),
    }


def evaluate_cases(cases: list[dict], k: int = 3) -> dict:
    """练习：每道题权重相同，返回汇总指标和逐题详情。

    cases 每条包含 case_id、query、expected_chunk_ids、retrieved_chunk_ids。
    query 仅用于展示；本函数不根据问题执行搜索，只评估提供的排名。
    不修改 cases，不吞掉单题异常，不跳过非法题目。
    """
    if type(k) is not int or k < 1:
        raise ValueError("k 必须是正整数")
    if not cases:
        raise ValueError("cases 不能为空")

    details = []
    hit_count = 0
    recall_sum = 0.0

    # TODO 1：遍历 cases。每轮调用 evaluate_retrieval，传入该题的
    # expected_chunk_ids、retrieved_chunk_ids 和 k，用 result 接收。
    for case in cases:
        result = evaluate_retrieval(
            expected_chunk_ids=case["expected_chunk_ids"],
            retrieved_chunk_ids=case["retrieved_chunk_ids"],
            k=k)
        details.append({"case_id": case["case_id"], "query": case["query"], **result})

    # TODO 2（在循环内）：
    # 如果 result["hit_at_k"] 为 True，hit_count 加 1。
    # 把 result["recall_at_k"] 累加到 recall_sum。
    # details 追加一个新字典，保留 case_id、query 和 result 中的三个字段。
    # 可以使用 {"case_id": case["case_id"], "query": case["query"], **result}。
        if result["hit_at_k"]:
            hit_count += 1
        recall_sum += result["recall_at_k"]
    # TODO 3（循环结束后）：返回字典，字段必须为：
    # k、case_count、hit_rate_at_k、mean_recall_at_k、details。
    # case_count 是 len(cases)。两个比率分别用 hit_count 和 recall_sum 除以题数。
    # 比率保留 0～1 的数值，不乘 100，不转字符串，不提前 round。
    case_count = len(cases)
    hit_rate_at_k = hit_count / case_count
    mean_recall_at_k = recall_sum / case_count
    return {
        "k": k,
        "case_count": case_count,
        "hit_rate_at_k": hit_rate_at_k,
        "mean_recall_at_k": mean_recall_at_k,
        "details": details,
    }


def demo_cases() -> list[dict]:
    """所有排名为演示数据；片段 ID 在此使用简写。"""
    return [
        {"case_id": "q1", "query": "练习角色住在哪里，喜欢什么？",
         "expected_chunk_ids": ["A", "B"], "retrieved_chunk_ids": ["C", "A", "D"]},
        {"case_id": "q2", "query": "另一位角色喜欢什么？",
         "expected_chunk_ids": ["C"], "retrieved_chunk_ids": ["A", "B", "D"]},
        {"case_id": "q3", "query": "示例地区有什么建筑？",
         "expected_chunk_ids": ["D"], "retrieved_chunk_ids": ["D", "A", "B"]},
    ]


def main() -> None:
    report = evaluate_cases(demo_cases(), k=3)
    print("以下是手写排名的离线指标，不代表真实模型效果：")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
