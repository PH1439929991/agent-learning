"""RAG 第四节：向量与余弦相似度。

本节向量全部是手工演示数据，不是模型输出，也不具备真实语义检索能力。
只完成 cosine_similarity() 的两个 TODO；不安装依赖、不请求模型。
运行：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.embedding_basics
"""

import math

from agent_learning.module_08_rag.neighbor_expansion import (
    expand_neighbors,
    make_demo_chunks,
)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """比较向量方向：点积 / (a 的长度 * b 的长度)。

    同方向为 1，垂直为 0，反方向为 -1；分数不是正确率或概率。
    输入约定是有限数值组成的非空列表；维度必须相同，不能是零向量。
    这里的“长度”指向量的数学长度，不是列表元素个数 len(a)。
    """
    if not a or len(a) != len(b):
        raise ValueError("向量不能为空，且两个向量的维度必须相同")
    norm_a = math.sqrt(sum(value * value for value in a))
    norm_b = math.sqrt(sum(value * value for value in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("零向量无法计算余弦相似度")

    # 删除占位异常，完成两个 TODO。
    #raise NotImplementedError("请完成 cosine_similarity 的两个 TODO")

    # TODO 1：计算点积 dot_product，即对应位置相乘，再全部相加。
    # 例如 a=[1, 2]，b=[3, 4]：点积 = 1*3 + 2*4 = 11。
    # 可以先设 dot_product = 0.0，再用 for x, y in zip(a, b) 累加。
    # zip(a, b) 会依次提供 (1, 3)、(2, 4)，不是计算所有位置的两两组合。
    dot_product = 0.0
    for x, y in zip(a, b):
        dot_product += x * y

    # TODO 2：返回 dot_product / (norm_a * norm_b)。括号不能省略。
    return dot_product / (norm_a * norm_b)

def rank_chunks(query_vector: list[float], chunks: list[dict]) -> list[dict]:
    """已完成：逐一打分，按分数从高到低排序；不修改原始片段。"""
    results = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk["embedding"])
        results.append({"chunk": chunk, "score": score})
    return sorted(results, key=lambda result: result["score"], reverse=True)


def main() -> None:
    cases = [
        ("同方向", [1.0, 0.0], [2.0, 0.0], 1.0),
        ("垂直", [1.0, 0.0], [0.0, 1.0], 0.0),
        ("反方向", [1.0, 0.0], [-1.0, 0.0], -1.0),
        ("一般情况", [1.0, 0.0], [3.0, 4.0], 0.6),
        ("多维点积", [1.0, 2.0], [3.0, 4.0], 11 / (math.sqrt(5) * 5)),
    ]
    for name, a, b, expected in cases:
        actual = cosine_similarity(a, b)
        assert math.isclose(actual, expected, abs_tol=1e-9), (name, actual)
        print(f"通过：{name}，分数={actual:.4f}")
    for a, b in [([], []), ([1.0], [1.0, 2.0]), ([0.0, 0.0], [1.0, 0.0])]:
        try:
            cosine_similarity(a, b)
        except ValueError:
            pass
        else:
            raise AssertionError("空向量、维度不一致或零向量应被拒绝")
    print("通过：无效输入检查")

    # 下面的数字是人为设计的，用来观察排序，不是文本自动生成的向量。
    # 真实使用时：问题和片段必须使用兼容的同一套 Embedding 模型/编码配置。
    vectors = {
        "yasuo_000": [0.6, 0.8, 0.0],
        "yasuo_001": [1.0, 0.0, 0.0],
        "yasuo_002": [0.8, 0.6, 0.0],
        "yasuo_003": [0.0, 0.0, 1.0],
        "ahri_001": [0.0, 1.0, 0.0],
    }
    chunks = [
        {**chunk, "embedding": vectors[chunk["chunk_id"]]}
        for chunk in make_demo_chunks()
    ]
    query_vector = [1.0, 0.0, 0.0]  # 手工模拟的问题向量
    results = rank_chunks(query_vector, chunks)
    print("\n演示向量排序（不是语义检索效果测评）：")
    for result in results:
        print(result["chunk"]["chunk_id"], f"score={result['score']:.4f}")

    best_hit = results[0]["chunk"]
    assert best_hit["chunk_id"] == "yasuo_001"
    # 排名第一不代表一定相关；真实检索还需要评估，必要时拒绝无关结果。
    neighbors = expand_neighbors(chunks, best_hit["chunk_id"], window=1)
    assert [c["chunk_id"] for c in neighbors] == ["yasuo_000", "yasuo_001", "yasuo_002"]
    print("最高分命中：", best_hit["chunk_id"])
    print("补取邻居后：", [c["chunk_id"] for c in neighbors])


if __name__ == "__main__":
    main()
