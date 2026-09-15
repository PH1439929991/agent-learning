"""RAG 第六节：建立内存向量索引，检索 Top-K 片段。

只完成 search_top_k() 的两个 TODO。默认运行只显示说明。
--live 会把所有切分片段及问题发给配置的 Embedding 服务，可能计费。
本节不调用聊天模型、不生成答案、不保存索引，也不自动补取邻居。
"""

import argparse

from agent_learning.module_08_rag.document_chunking import load_documents
from agent_learning.module_08_rag.embedding_basics import rank_chunks
from agent_learning.module_08_rag.overlapping_chunking import build_overlapping_chunks
from agent_learning.module_08_rag.real_embeddings import create_embedding_client, embed_text


def build_vector_index(client, model: str, chunks: list[dict]) -> list[dict]:
    """已完成：每个片段编码一次，返回带 embedding 的新片段列表。

    这是简单的内存索引：仍然是 Python 列表，不是向量数据库。
    本节逐条请求，便于观察；批量请求和持久化缓存后面再学。
    """
    index = []
    for chunk in chunks:
        vector = embed_text(client, model, chunk["text"])
        # **chunk 复制原字典中的字段，再增加 embedding，不修改原字典。
        index.append({**chunk, "embedding": vector})
    return index


def search_top_k(
    query_vector: list[float], index: list[dict], top_k: int = 3
) -> list[dict]:
    """返回分数最高的 K 条结果，每条为 {"chunk": 完整片段, "score": 分数}。

    top_k 必须为正整数；索引为空返回 []；K 超过片段数时返回全部。
    问题和索引必须由兼容的同一套 Embedding 模型/配置生成。
    不修改输入列表，不重新请求片段向量；排名第一也不保证包含答案。
    """
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k 必须是正整数")
    if not index:
        return []

    # TODO 1：调用 rank_chunks(query_vector, index)，用 results 接收
    # 按相似度从高到低排列的全部结果。这个函数已经从第四节导入。
    results = rank_chunks(query_vector, index)
    # TODO 2：使用列表切片，返回 results 的前 top_k 条。
    # 提示：items[:2] 取前两条；这里应使用参数 top_k，不能写死为 2 或 3。
    # 不要只返回 chunk_id，保留结果中的 chunk 和 score。
    return results[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser(description="英雄资料 Top-K 向量检索练习")
    parser.add_argument("--live", action="store_true", help="发送真实 Embedding 请求")
    parser.add_argument("--query", default="我想了解亚索的背景故事。")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if args.top_k < 1 or not args.query.strip():
        parser.error("top-k 必须大于等于 1，query 不能为空")
    if not args.live:
        print("请先完成 search_top_k() 的两个 TODO，并运行配套离线测试。")
        print("加 --live 后会发送所有英雄片段及问题；不是上一节的三句短文本。")
        print("每次重启都会重新编码资料，可能计费；本节未做缓存。")
        return

    documents = load_documents()
    chunks = build_overlapping_chunks(documents, chunk_size=300, overlap=50)
    if not chunks:
        print("没有可检索的资料，本次不请求模型。")
        return
    print(f"将编码 {len(chunks)} 个片段和 1 个问题，正常完成共 {len(chunks) + 1} 次请求。", flush=True)
    client, model = create_embedding_client()
    try:
        # 建索引：在本次进程中准备资料向量。
        index = build_vector_index(client, model, chunks)
        # 查问题：同一个 client、model 编码问题，只需一次。
        query_vector = embed_text(client, model, args.query)
        # 打分排序全部在本地计算，不再请求模型。
        hits = search_top_k(query_vector, index, top_k=args.top_k)
        print("问题：", args.query)
        for rank, hit in enumerate(hits, start=1):
            chunk = hit["chunk"]
            print(f"\n第 {rank} 名 | {chunk['chunk_id']} | 相似度 {hit['score']:.4f}")
            print("英雄：", chunk["metadata"]["champion_name"])
            print("片段：", chunk["text"])
            print("来源（原资料标注，未核验）：", chunk["metadata"].get("source_url", ""))
    finally:
        client.close()


if __name__ == "__main__":
    main()
