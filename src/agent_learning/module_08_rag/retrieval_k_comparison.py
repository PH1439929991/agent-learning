"""第十四节：复用一次检索排名，对比不同 K。默认演示完全离线。

只填写 compare_top_k 的三个 TODO，不修改前几节。
这里复用的是一次运行中的排名，不是跨运行的问题向量缓存。
"""

import json
from typing import Callable

from agent_learning.module_08_rag.retrieval_benchmark import collect_retrieval_results
from agent_learning.module_08_rag.retrieval_evaluation import evaluate_cases


def compare_top_k(
    cases: list[dict], retrieve: Callable[[str, int], list[dict]], ks: list[int],
) -> list[dict]:
    """练习：每题只检索一次，返回按 K 升序排列的完整评测报告。

    输入：cases 是标注问题列表；retrieve 是检索函数；ks 例如 [3, 1, 2, 3]。
    中间：去重排序得 [1, 2, 3]，每题取一次 Top-3，复用该排名。
    输出：每个 K 对应一份 evaluate_cases 报告，保留 details，不只返回分数。

    前提：同一检索方式下取固定排名的不同前缀。本项目的精确余弦排序满足此条件。
    如果检索过程、过滤或重排策略随 K 改变，就不能这样替代独立实验。
    """
    if not cases:
        raise ValueError("cases 不能为空")
    if not ks or any(type(k) is not int or k < 1 for k in ks):
        raise ValueError("ks 必须包含正整数，且不能为空")

    # TODO 1：用 sorted(set(ks)) 得到 unique_ks，再取其中最大值 max_k。
    unique_ks = sorted(set(ks)) #应该从小到大排序
    max_k = unique_ks[-1]

    # TODO 2：在 K 的循环之外，调用一次
    # collect_retrieval_results(cases, retrieve, max_k)，用 ranked_cases 接收。
    # 它内部会为每道题调用一次 retrieve。不要为每个 K 重新调用它。
    ranked_cases = collect_retrieval_results(cases, retrieve, max_k)

    # TODO 3：创建 reports，遍历 unique_ks。
    # 把 evaluate_cases(ranked_cases, k) 的结果追加到 reports。
    # evaluate_cases 内部会按当前 k 截断排名，无需你修改 ranked_cases。
    # 循环结束后返回 reports。
    reports = []
    for k in unique_ks:
        report = evaluate_cases(ranked_cases, k)
        reports.append(report)

    return reports


def main() -> None:
    cases = [{"case_id": "q1", "query": "练习角色住在哪里，喜欢什么？",
              "expected_chunk_ids": ["A", "B"]}]

    def fake_retrieve(query: str, k: int) -> list[dict]:
        print(f"假检索收到：query={query!r}, k={k}")
        # 手写排名，仅验证计算逻辑，不代表真实模型表现。
        return [{"chunk": {"chunk_id": chunk_id}} for chunk_id in ["X", "A", "B"][:k]]

    reports = compare_top_k(cases, fake_retrieve, [1, 2, 3])
    print("各 K 的完整报告：")
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
