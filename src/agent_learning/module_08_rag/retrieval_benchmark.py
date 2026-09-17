"""第十三节：固定标注问题 → 实际检索 → 多题指标。

只实现 collect_retrieval_results 的三个 TODO。默认不请求模型。
--live：复用已有资料索引，每题一次 Embedding，不生成聊天答案、不重建索引。
"""

import argparse
import json
from pathlib import Path
from typing import Callable

from agent_learning.module_08_rag.document_chunking import load_documents
from agent_learning.module_08_rag.index_persistence import (
    DEFAULT_INDEX_PATH, load_index, source_fingerprint, validate_index,
)
from agent_learning.module_08_rag.overlapping_chunking import build_overlapping_chunks
from agent_learning.module_08_rag.real_embeddings import create_embedding_client, embed_text
from agent_learning.module_08_rag.retrieval_evaluation import evaluate_cases
from agent_learning.module_08_rag.top_k_retrieval import search_top_k


# 2026-09-17 阅读当前 14 个片段后标注；仅评价本地学习资料，不认证英雄设定。
SOURCE_HASH = "67a0e70c456c8d030191794b5e9d77c5c62f5e66f7df43aa7f9a2b7bd2e2635c"
BENCHMARK_CASES = [
    {"case_id": "lulu_partner", "query": "根据学习资料，璐璐的仙灵旅伴叫什么？",
     "expected_chunk_ids": ["lulu_000"],
     "evidence": {"lulu_000": "皮克斯是璐璐最亲密的旅伴"}},
    {"case_id": "nautilus_tax", "query": "根据学习资料，诺提勒斯追索的是哪种海洋贡税？",
     "expected_chunk_ids": ["nautilus_000"],
     "evidence": {"nautilus_000": "征收海洋什一税"}},
    {"case_id": "kennen_lulu", "query": "根据学习资料，凯南和璐璐分别有什么能力？",
     "expected_chunk_ids": ["kennen_000", "lulu_000"],
     "evidence": {"kennen_000": "能够驾驭雷电", "lulu_000": "能让事物发生奇妙变形"}},
]


def collect_retrieval_results(
    cases: list[dict], retrieve: Callable[[str, int], list[dict]], k: int = 3,
) -> list[dict]:
    """练习：给每道题添加实际 retrieved_chunk_ids，保留原来的标注。

    retrieve 是函数：retrieve(query, k) 返回 [{"chunk": {...}, "score": ...}, ...]。
    测试时传入假函数；live 时传入“问题 Embedding + search_top_k”的真实函数。
    本函数不需要知道 API Key 或向量细节，只负责调用并提取 ID。
    """
    if type(k) is not int or k < 1:
        raise ValueError("k 必须是正整数")
    if not cases:
        raise ValueError("cases 不能为空")
    # 先检查所有题，避免前几题付费后才发现后面的题缺参数。
    for case in cases:
        if not case["query"].strip() or not case["expected_chunk_ids"]:
            raise ValueError("题目必须包含非空问题和预期片段")

    # TODO 1：创建 results = []，遍历 cases。
    # 每轮调用 retrieve(case["query"], k)，用 hits 接收。
    results = []
    for case in cases:
        hits = retrieve(case["query"], k)
        retrieved_ids = [hit["chunk"]["chunk_id"] for hit in hits]
        results.append({**case, "retrieved_chunk_ids": retrieved_ids})

    # TODO 2（循环内）：从 hits 按原排名提取 hit["chunk"]["chunk_id"]，
    # 得到 retrieved_ids。不要重新排序，不要用 expected_chunk_ids 冒充结果。
    # 把 {**case, "retrieved_chunk_ids": retrieved_ids} 追加到 results。
    # 使用新字典，不直接给 case 赋值。
    # TODO 3：循环结束后返回 results。
    return results


def validate_benchmark(chunks: list[dict]) -> None:
    """已完成：资料版本改变需重新阅读和标注，不能直接改 hash 绕过。"""
    if source_fingerprint(chunks) != SOURCE_HASH:
        raise ValueError("资料或切分已变化，请重新核对评测标注")
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    for case in BENCHMARK_CASES:
        for chunk_id in case["expected_chunk_ids"]:
            if chunk_id not in by_id or case["evidence"][chunk_id] not in by_id[chunk_id]["text"]:
                raise ValueError("预期片段或标注依据已失效")


def main() -> None:
    parser = argparse.ArgumentParser(description="固定问题集的真实检索评测")
    parser.add_argument("--live", action="store_true", help="允许对每个问题请求一次 Embedding")
    parser.add_argument("--index-file", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("top-k 必须是正整数")
    if not args.live:
        print("请先完成 collect_retrieval_results 并通过离线测试。")
        print("--live 将读取已有索引，发送 3 个标注问题，可能计费；不重建、不生成答案。")
        return

    # 本地预检查：TODO 未完成或前一节汇总未完成时，在付费前报错。
    preflight = collect_retrieval_results(BENCHMARK_CASES, lambda query, k: [], args.top_k)
    evaluate_cases(preflight, args.top_k)
    chunks = build_overlapping_chunks(load_documents(), 300, 50)
    validate_benchmark(chunks)
    payload = load_index(args.index_file)
    client, model = create_embedding_client()
    try:
        validate_index(payload, model, str(client.base_url), chunks)

        def retrieve(query: str, k: int) -> list[dict]:
            query_vector = embed_text(client, model, query)
            return search_top_k(query_vector, payload["chunks"], k)

        results = collect_retrieval_results(BENCHMARK_CASES, retrieve, args.top_k)
        report = evaluate_cases(results, args.top_k)
        print(json.dumps({
            "model": model, "source_hash": SOURCE_HASH,
            "rankings": [{"case_id": row["case_id"],
                          "retrieved_chunk_ids": row["retrieved_chunk_ids"]} for row in results],
            "report": report,
        }, ensure_ascii=False, indent=2))
        print("这只是三题学习用小样本结果，不代表完整资料库效果或回答正确率。")
    finally:
        client.close()


if __name__ == "__main__":
    main()
