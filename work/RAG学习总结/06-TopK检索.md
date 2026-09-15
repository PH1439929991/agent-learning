# 第六节：Top-K 检索

代码：[top_k_retrieval.py](../../src/agent_learning/module_08_rag/top_k_retrieval.py)

## 核心流程

先把资料按 chunk_size 和 overlap 切成片段；再给每段生成向量，形成 index。用户提问时生成 query_vector，与索引中向量打分排序，取前 K 条。

chunk 通常是列表中的字典，不是每段一个文件：

```python
{
    "chunk_id": "yasuo_000",
    "document_id": "yasuo",
    "text": "资料正文",
    "metadata": {"champion_name": "亚索"},
    "embedding": [0.1, 0.2],  # 仅示例，不是真实向量
}
```

build_vector_index 使用 {**chunk, "embedding": vector} 创建带向量的新字典，不修改原片段。

search_top_k 调用 rank_chunks 排序，再返回 results[:top_k]。每条命中保留完整结构：

```python
{"chunk": 完整片段字典, "score": 相似度}
```

## 容易混淆的地方

- top_k=3 是最多三个片段，不是三位英雄；全库不足三条时返回实际数量。
- window=1 是命中后补取同一文档前后邻居，不负责向量排名。
- Top-K 已包含按相似度排序；额外 reranker 是另一个可选步骤，当前未接入。
- 排名第一不保证包含答案，后面的命中也可能来自无关英雄。
- 此文件 --live 每次都会重新编码全库；有缓存后应改用第七节查询入口。

## 验证

9 个离线测试通过，覆盖排序、K 的边界、空索引、不修改输入和建索引。

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_top_k_retrieval.py -q
```
