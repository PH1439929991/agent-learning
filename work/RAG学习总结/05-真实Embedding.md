# 第五节：真实 Embedding

代码：[real_embeddings.py](../../src/agent_learning/module_08_rag/real_embeddings.py)

## 学到了什么

Embedding 把文本编码成数字列表。模型通过训练得到参数，新输入通过这些参数计算向量；不是每次提问重新训练，也不是查找预先保存好的所有句子。

向量的整体方向和距离可用于相似度比较，不能随意把单个维度解释为某个固定语义。余弦相似度是点积除以两向量的数学长度乘积，不是除以列表元素数量；得分不是正确率。

## 代码执行顺序

1. create_embedding_client 读取 EMBEDDING_API_KEY、EMBEDDING_BASE_URL、EMBEDDING_MODEL。
2. embed_text 检查文本非空，发送 model、input、encoding_format。
3. 返回 response.data[0].embedding，也就是一组浮点数。
4. 本地计算候选文本与问题的相似度并排序。

聊天接口用 messages；Embedding 接口用 input，不需要 system prompt。聊天模型名不能直接当 Embedding 模型使用，404 需要检查服务地址与模型是否支持该接口。

## 本次验证

2026-09-15 使用硅基流动 Qwen/Qwen3-Embedding-0.6B，观察到 1024 维向量。问题“我想了解亚索的背景故事。”与两条候选的分数：

- “关于亚索身世与经历的资料。”：约 0.8329。
- “如何烹饪意大利面。”：约 0.2718。

这是本次观察，不是固定的测试预期。三段文本正常完成共三次真实请求。

## 运行注意

项目根目录运行，不要在 module_08_rag 目录里使用根目录的相对路径：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.real_embeddings
```

默认不请求；加 --live 才发真实请求，可能计费。本节不保存向量，反复运行 live 会重复编码。
