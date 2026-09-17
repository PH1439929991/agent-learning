# 第十七节：完整 RAG 与真实验收

验收日期：2026-09-17。主流程由你完成；本次补上真实接口适配器。

## 1. 先抓住核心

`run_rag()` 不关心模型客户端怎么创建，只要求你提供两个函数：

| 回调 | 输入 | 输出 | 本次真实实现 |
| --- | --- | --- | --- |
| `retrieve` | 问题字符串、k | `[{"chunk": 完整片段, "score": 相似度}, ...]` | 问题 Embedding + 本地 Top-K |
| `generate` | 已经过预算选择的 messages | 答案字符串 | 一次 DeepSeek 聊天请求 |

所以，离线测试和真实运行用的是同一个 `run_rag()`。变化的是两个回调，不是整套 RAG 逻辑。

代码入口：

- [rag_pipeline.py](../../src/agent_learning/module_08_rag/rag_pipeline.py)：你已经完成的主流程。
- [rag_live_acceptance.py](../../src/agent_learning/module_08_rag/rag_live_acceptance.py)：真实适配器与三个固定问题。
- [test_rag_live_acceptance.py](../../src/agent_learning/module_08_rag/test_rag_live_acceptance.py)：离线检查请求参数、次数和失败路径。

## 2. 用第二题看输入、中间结果、输出

输入问题：`根据学习资料，凯南和璐璐分别有什么能力？`

1. 加载现有索引，并检查模型、服务地址、资料指纹、正文和向量格式。不一致就停止，不自动建库。
2. `retrieve(query, 3)`：只把这个问题发给 Embedding 服务，得到 1024 维问题向量。
3. 与本地资料向量比较，实际返回下面的排名。

| 排名 | chunk_id | 余弦相似度（四舍五入） |
| --- | --- | --- |
| 1 | kennen_000 | 0.5831 |
| 2 | lulu_000 | 0.5802 |
| 3 | katarina_000 | 0.4536 |

4. 邻居扩展和去重补入 `katarina_001`；`prioritize_hits()` 保证直接命中在前。
5. `select_context()` 检查完整消息大小：1764 字符，小于 6000 字符预算，四段全部保留。
6. 形成下面的来源映射，把 `selection["messages"]` 原样交给 `generate()`。

| messages 中的来源编号 | 对应 chunk_id |
| --- | --- |
| [1] | kennen_000 |
| [2] | lulu_000 |
| [3] | katarina_000 |
| [4] | katarina_001 |

真实答案摘录：

> 根据学习资料：
>
> **凯南的能力**：行动迅捷，能够驾驭雷电 [1]。
>
> **璐璐的能力**：能让事物发生奇妙变形，也常把幻想与现实混合在一起 [2]。

7. `finish_run()` 检查引用 `[1]`、`[2]` 是否处于 1～4 范围，并返回答案、来源和检查报告。

返回报告的关键字段：

```python
{
    "status": "generated",
    "retrieved_ids": ["kennen_000", "lulu_000", "katarina_000"],
    "source_ids": ["kennen_000", "lulu_000", "katarina_000", "katarina_001"],
    "omitted_ids": [],
    "source_count": 4,
    "input_size": 1764,      # 本地字符计数，不是 Token！
    "input_budget": 6000,
    "citation_check": {
        "cited_numbers": [1, 2], "invalid_numbers": [],
        "has_citations": True, "references_valid": True,
    },
    # 还有 answer、messages 等字段；这里省略长正文。
}
```

## 3. 三组真实结果

| 用例 | 用户问题 | 实际结果与人工检查 |
| --- | --- | --- |
| 单资料 | 根据学习资料，璐璐的仙灵旅伴叫什么？ | 回答皮克斯，引用 [1]，与 lulu_000 一致 |
| 多资料 | 根据学习资料，凯南和璐璐分别有什么能力？ | 分别使用 kennen_000、lulu_000，引用 [1]、[2]，主要陈述有本地资料支持 |
| 资料不足 | 根据学习资料，璐璐第一次遇见皮克斯的确切公历日期（年月日）是什么？ | 明确没有确切日期，未编造年月日 |

第一题完整答案：

> 根据学习资料，璐璐的仙灵旅伴叫皮克斯 [1]。资料中称皮克斯是璐璐的“仙灵伙伴”和“最亲密的旅伴” [1]。

第三题完整答案：

> 根据学习资料，璐璐遇见皮克斯的事件有记载，但资料中没有给出确切公历日期（年月日）[1]。资料只提到璐璐追随神秘仙灵皮克斯，踏入了一个充满原始魔法的奇异世界[1]。因此，资料不足，无法回答确切日期。

第一题和第三题的 Top-3 都是 `lulu_000、yasuo_001、zoe_000`，扩展后补入 `yasuo_000`，来源 [1] 为 lulu_000。三题都保留了四段，均未触发预算舍弃，结束原因均为 `stop`。

第二题还多说了“资料中未提及……具体细节或强度对比”。这是用户未追问的保守补充，略显多余；不把接口成功当成回答完美。

## 4. 字符数与实际 Token 对比

| 用例 | 本地输入字符数 | 接口 prompt_tokens | completion_tokens | total_tokens | 本次端到端耗时 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 单资料 | 1646 | 970 | 42 | 1012 | 3.466 秒 |
| 多资料 | 1764 | 1010 | 139 | 1149 | 1.263 秒 |
| 资料不足 | 1661 | 978 | 61 | 1039 | 1.120 秒 |

聊天接口合计：输入 2958 Token，输出 242 Token，总计 3200 Token。不包含 Embedding 用量；没有据此估算账单金额。耗时只是这次观测，不是性能保证。

共完成 3 次问题 Embedding、3 次聊天请求，未自动重试。没有重新计算 14 段资料向量，索引文件 SHA-256 在运行前后保持不变。

Embedding 配置：`Qwen/Qwen3-Embedding-0.6B`；聊天请求仍使用原配置 `deepseek-v4-flash`，接口实际返回的 model 为 `deepseek-flash`。没有改 .env 或擅自换模型；记录请求名和响应名，不假设别名永远对应同一版本。

资料指纹：`67a0e70c456c8d030191794b5e9d77c5c62f5e66f7df43aa7f9a2b7bd2e2635c`。

## 5. 三个最容易混淆的点

1. **检索到资料 ≠ 资料包含答案。** 第三题命中了璐璐资料，但正文没有日期；仍然需要模型根据证据拒答。它的 status 也是 generated，因为确实请求了模型。
2. **Top-K ≠ 最终来源数。** 本次 Top-3 经邻居扩展后有 4 段，所以引用检查使用 source_count=4，而不是 top_k=3。
3. **引用编号合法 ≠ 事实正确。** 三题编号检查都通过，我们还人工对照了正文。英雄资料没有做官方事实核验，这次只验证与本地学习资料的一致性。合理拒答也可能没有引用，不能机械地当作回答错误。

额外观察：检索前三不全都相关，第一题仍混入亚索、佐伊；邻居扩展还可能放大无关内容。这解释了为什么项目中要评测 K、扩展窗口和预算，而不是一味加大。这里没有独立重排模型。

## 6. 如何自己运行

在项目根目录执行，默认不联网：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_live_acceptance
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_rag_pipeline.py src/agent_learning/module_08_rag/test_rag_live_acceptance.py -q
```

想重新观察真实输出时再加 `--live`。每执行一次都可能计费；无需为了阅读结果再运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_live_acceptance --live
```

本次聊天适配器关闭 SDK 自动重试，设置 20 秒网络超时和 1024 Token 输出上限，并关闭 DeepSeek 思考模式。网络超时不是整个程序的严格总时限。输入仍是教学字符预算，尚未实现对应模型的精确 Token 预算。

根据 OpenAI Docs 核对了消息和 usage 的接口结构；输出限制、思考开关以实际服务商 DeepSeek 的文档为准，不混用两家的参数规则：

- [OpenAI Chat Completions Python 参考](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create)
- [DeepSeek Chat Completions 参数](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)

## 7. 现在你来解释

不用再写大段代码，先回答三个问题：

1. 第三题为什么检索成功，却不能回答确切日期？
2. top_k=3，为什么 source_count=4？
3. 把假客户端换成真实客户端，为什么不用重写 run_rag？

第十七节的三类真实样例已验收；这不是大规模质量评测，也没有执行第十三节那套固定检索评测集。下一节按计划将检索能力接成 Agent 工具，不再拆更多基础小节。
