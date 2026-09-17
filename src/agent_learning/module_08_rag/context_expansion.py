"""第十五节：多条命中补取邻居，并按片段 ID 去重。纯离线。

只完成 expand_context_chunks 的三个 TODO。复用第三节的 expand_neighbors。
不重新检索、不合并重叠文字、不重新打分，本节暂不加入 Token 预算。
"""

from agent_learning.module_08_rag.neighbor_expansion import expand_neighbors
from agent_learning.module_08_rag.rag_answering import build_rag_messages


def expand_context_chunks(
    chunks: list[dict], hits: list[dict], window: int = 1,
) -> list[dict]:
    """练习：返回扩展去重后的完整片段字典列表，不修改输入。

    chunks：同一版本资料的全部片段，ID 必须唯一，可乱序。
    hits：按检索排名排列的命中列表，每条有 hit['chunk']。
    window：同一篇文档前后各补多少段；0 表示仅保留命中并去重。

    顺序规则：按 hits 顺序处理；每次邻居按原文顺序返回；重复 ID 只留首次。
    这是首次出现顺序，不保证最终全局按文档序号排序，也不是新的相似度排名。
    """
    if type(window) is not int or window < 0:
        raise ValueError("window 必须是非负整数")
    all_ids = [chunk["chunk_id"] for chunk in chunks]
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("chunks 的 chunk_id 必须唯一")
    if not hits:
        return []

    # TODO 1：创建 selected = [] 和 seen_ids = set()。
    # 按顺序遍历 hits，调用 expand_neighbors(chunks, 命中的chunk_id, window)，
    # 用 neighbors 接收。只传 hits 给 expand_neighbors 会漏掉未命中的邻居！
    selected = []
    seen_ids = set()
    for hit in hits:
        neighbors = expand_neighbors(chunks, hit["chunk"]["chunk_id"], window)

        for i in neighbors:
            if i["chunk_id"] not in seen_ids:
                selected.append(i)
                seen_ids.add(i["chunk_id"])

    # TODO 2：在外层循环内遍历 neighbors。
    # 若当前 chunk['chunk_id'] 不在 seen_ids 中：
    # 将完整 chunk 追加到 selected，并用 seen_ids.add(...) 记录该 ID。
    # 不要只返回 ID，也不要给邻居复制命中段的 score。

    # TODO 3：两个循环结束后返回 selected。
    return selected


def make_example() -> tuple[list[dict], list[dict]]:
    """手写片段与命中：A_001 的解释位于下一段 A_002。"""
    rows = [
        ("A", 2, "原因是当地设有图书馆，便于学习。"),
        ("B", 1, "另一篇文档：角色喜欢游泳。"),
        ("A", 0, "背景：练习角色正在选择居住地。"),
        ("A", 3, "他也喜欢参加读书交流活动。"),
        ("A", 1, "他最终选择住在示例地区，原因如下。"),
    ]
    chunks = [{
        "chunk_id": f"{doc}_{i:03d}", "document_id": doc, "text": text,
        "metadata": {"chunk_index": i, "champion_name": "练习角色",
                     "source_file": "离线演示"},
    } for doc, i, text in rows]
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    hits = [{"chunk": by_id["A_001"], "score": 0.9},
            {"chunk": by_id["A_002"], "score": 0.8}]
    return chunks, hits


def main() -> None:
    chunks, hits = make_example()
    print("输入命中：", [hit["chunk"]["chunk_id"] for hit in hits])
    for hit in hits:
        neighbors = expand_neighbors(chunks, hit["chunk"]["chunk_id"], 1)
        print("单次扩展：", hit["chunk"]["chunk_id"], "→",
              [chunk["chunk_id"] for chunk in neighbors])
    selected = expand_context_chunks(chunks, hits, window=1)
    print("去重后的输出：", [chunk["chunk_id"] for chunk in selected])

    # 第八节的消息函数只读取 chunk，不依赖 score；给邻居构造所需外层包装即可。
    # 这是消息准备阶段，不把扩展结果冒充原始 Top-K 排名。
    context_hits = [{"chunk": chunk} for chunk in selected]
    messages = build_rag_messages("练习角色为什么选择示例地区？", context_hits)
    print("最终提供的资料条数：", len(context_hits))
    print("user 消息：\n", messages[1]["content"])
    print("以上只是消息展示，没有调用聊天或 Embedding 模型。")


if __name__ == "__main__":
    main()
