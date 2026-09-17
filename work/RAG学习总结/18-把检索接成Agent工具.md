# 第十八节：把检索接成 Agent 工具

进度更新（2026-09-17）：你已完成 [rag_search_tool.py](../../src/agent_learning/module_08_rag/rag_search_tool.py) 的三个 TODO，13 个测试通过；单次真实工具问答也已跑通，实际输入输出见第 7 部分。旧章节源码未修改。

## 1. 与第十七节有什么不同？

第十七节：程序主动运行整套 RAG，检索后调用 generate 生成答案。

第十八节：Agent 模型决定调用检索工具，工具返回资料，再由 Agent 模型生成答案。

因此不把 `run_rag()` 整个塞进检索工具：其中的 `finish_run()` 会调用生成器，而这次工具只需要“找资料”。这是一种职责划分，不是说工具内部永远不能调用模型。

本题先接最小 Top-K 检索版本，暂不加邻居扩展和预算选择。第十七节完整流程仍保留。生产使用时，预算要覆盖整个 Agent messages、工具说明与工具结果，不能把第十七节的字符预算直接当作 Agent 总 Token 预算。

## 2. 输入 → 中间结果 → 输出

假设用户问：`练习角色住在哪里？`

第一次模型请求：messages 只有 system 和 user，同时通过 tools 参数提供工具说明。

模型可能返回以下工具调用（教学示意，真实验收记录见第 7 部分）：

```python
{
    "id": "call_search_001",
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "arguments": '{"query": "练习角色住在哪里？", "top_k": 1}',
    },
}
```

执行器按你之前学过的顺序处理：先 json.loads，再查注册表，再 Pydantic 校验，最后调用 Python 函数。

函数中 `retrieve(query, top_k)` 返回的 hits 示意：

```python
[
    {
        "chunk": {"chunk_id": "demo_000", "text": "练习角色住在示例地区。"},
        "score": 0.9,
    }
]
```

你要把 hits 整理成下面的工具结果：

```python
{
    "success": True,
    "query": "练习角色住在哪里？",
    "sources": [
        {"chunk_id": "demo_000", "text": "练习角色住在示例地区。"}
    ],
    "source_count": 1,
}
```

不返回向量：向量用于检索比较，模型作答需要的是正文。不在这里生成最终答案。

旧 Agent 循环会自动把这个字典转为 JSON 字符串，追加进 messages：

```python
{
    "role": "tool",
    "tool_call_id": "call_search_001",
    "content": json.dumps(工具返回的字典, ensure_ascii=False),
}
```

第二次模型请求的消息顺序是 system、user、assistant 的工具调用、tool 的资料结果。一轮工具调用通常需要这两次模型请求，不能把两次模型请求误认为调用了两次检索工具。

在本题的模型替身中，最后返回：`根据学习资料，练习角色住在示例地区。[demo_000]`。这是测试预设答案，不是真实生成结果。

## 3. 你只填写三个 TODO

1. 调用 `retrieve(query, top_k)`，得到 hits。
2. 遍历 hits，取 `hit["chunk"]`，把 chunk_id、text 两个字段放进 sources 中的新字典。保持顺序，不改原片段。
3. 返回 success、query、sources、source_count 四个字段。

完成后删除占位的 `raise NotImplementedError(...)`。

没有命中时也返回 success=True、sources=[]、source_count=0：本次检索执行成功，只是没取到资料。不要据此声称全库或现实世界都没有答案。

## 4. 注册和校验已经帮你准备好

`SearchKnowledgeArguments` 定义 query 必填，去掉首尾空格后不能为空；top_k 默认 3，只允许整数 1～5。拒绝额外参数，布尔值和字符串数字也不当作整数接受。

`build_registration(retrieve)` 返回两个东西：Python 执行器使用的 registry，以及发给模型的 tools。这里的 wrapper 把 retrieve 函数保留在程序内部，所以 schema 中只有 query 和 top_k。模型不能指定 Python 函数地址。

测试用 monkeypatch 临时把这两个对象接入第四章 Agent，不修改其源码。测试结束自动恢复，不会影响其他章节。

本题使用 chunk_id 引用，例如 `[demo_000]`，便于区分多次工具检索的片段；不复用每次都从 1 开始的临时编号。第九节的数字引用检查器不支持这种引用，本题尚未实现新的自动引用检查，不能把没有报错当成引用已验证。

## 5. 运行和预期

在项目根目录运行演示：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_search_tool
```

它会显示 schema、检索参数和工具返回值，不请求模型。

运行本题测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_rag_search_tool.py -q
```

你完成 TODO 后，13 个检索工具测试已全部通过。真实入口另外有 14 个离线护栏测试，均通过。

这四个练习测试分别检查：返回资料不带向量且不改原数据、空检索、执行器应用默认参数和去空格、真实 Agent 循环把资料带入第二次模型请求。

本机第八章测试共 140 个通过（排除尚未同步的第十节旧练习）；连同第五章 Agent 测试共 150 个通过。真实入口默认不联网，需显式添加 --live。

## 6. 学完能解释什么？

- 模型只提出工具调用，真正执行 Python 函数的是谁？
- 工具为什么返回正文，而不是 embedding 数组或最终答案？
- tools、registry、role=tool 的消息分别有什么作用？
- 工具调用后，为什么还要再请求一次模型？

本节按 OpenAI Docs 技能核对了 Chat Completions 的工具回传方式：assistant 工具调用和 tool 结果通过 tool_call_id 对应，再交给模型继续回答。参见 [官方 Function calling 指南](https://developers.openai.com/api/docs/guides/function-calling)。实际服务参数按 [DeepSeek 接口文档](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/) 核对。

## 7. 真实验收：看每一轮输入和输出

入口：[rag_agent_live.py](../../src/agent_learning/module_08_rag/rag_agent_live.py)。这是限定一次检索的验收流程，不替换第四章的通用工具循环，也不修改其全局注册表。

### 第一轮：模型决定查什么

用户问题：`根据学习资料，璐璐的仙灵旅伴叫什么？`

传入 messages：system 规则、user 问题。tools 提供 search_knowledge 的说明，tool_choice="auto"，不强制调用工具。

模型实际返回：

```python
{
    "id": "call_00_pCUUxG8QYWToTYy2eMig7663",
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "arguments": '{"query": "璐璐的仙灵旅伴叫什么"}',
    },
}
```

注意：模型改写了检索 query，并且没有传 top_k。Pydantic 校验后补上默认值：

```python
{"query": "璐璐的仙灵旅伴叫什么", "top_k": 3}
```

应用程序按注册表执行你写的工具；不是模型直接运行 Python。

### 工具执行：只计算一个问题向量

读取并验证已有 14 段索引，不重新编码资料。把模型提出的 query 送给 Embedding 服务，得到 1024 维向量。

本次 Top-3 排名：

- lulu_000：0.6839。
- yasuo_001：0.4488。
- zoe_000：0.4449。

返回 success=True、source_count=3，以及这三段的 chunk_id 和完整正文。工具内部没有聊天请求；本题没有邻居扩展，所以不会像第十七节那次一样变成 4 段。

### 第二轮：把工具资料交给模型回答

传入 messages 共四条，顺序如下：

1. system：回答规则。
2. user：原始用户问题。
3. assistant：上面的工具调用记录。
4. tool：检索结果的 JSON 字符串，tool_call_id 与上面的 id 一致。

本次明确设置 tool_choice="none"，要求到此作答，不再调用其他工具。程序也会拒绝第三次请求。因此这只验证了“自动选择一次工具后作答”，不证明多轮自主路由或多个工具间选择的效果。

模型真实回答：

> 根据学习资料，璐璐的仙灵旅伴叫**皮克斯**。资料中称“她和仙灵伙伴皮克斯一起旅行”，并在相关人物中注明“皮克斯（仙灵伙伴）。皮克斯是璐璐最亲密的旅伴，也是引领她接触仙灵魔法的重要伙伴” [lulu_000]。

人工对照：lulu_000 的正文确实支持该答案，引用 ID 也在工具返回值中。这不是自动语义校验，也没有验证英雄资料的官方真实性。

### 次数和用量

- 第一轮聊天：输入 543、输出 55，共 598 Token；结束原因 tool_calls。
- 问题 Embedding：1 次，1024 维；未统计其账单用量。
- 第二轮聊天：输入 713、输出 70，共 783 Token；结束原因 stop。
- 聊天合计 1381 Token，不含 Embedding。没有自动重试。
- 请求仍使用配置中的 deepseek-v4-flash，服务实际返回 model=deepseek-flash；未修改模型配置。
- 索引文件 SHA-256 前后同为 d38c1085cf1e9a4e78b20d213b76eb50d95f8cd0fe63b0113ebefaf2606574b6，未重建或覆盖。

输入 JSON 的本地字符计数分别为 921、2127，与实际 Token 统计不是同一个单位。入口有 12000 字符护栏、单次输出 1024 Token 上限、20 秒网络超时和零自动重试；尚非精确的全上下文 Token 管理，网络超时也不是整个程序的严格时限。

### 自己重跑

先看默认说明，不会联网：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_agent_live
```

显式允许真实请求（每次可能计费，阅读本文无需重跑）：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_agent_live --live
```

默认就是本次璐璐问题；可用 --question 指定问题。每次最多两次聊天、一次问题 Embedding。多工具调用、参数不合法、超时、输出截断等情况直接停止，不隐藏错误或自动追加付费请求。

第八章的基础练习到此收尾：你已走过切分、向量化、缓存检索、带资料回答、引用与评测、预算，以及把检索接成工具。仍未完成的生产能力（精确 Token 管理、工具 ID 引用自动检查、多轮真实路由评测等）保留为项目改进项，不把这一个成功样例当成生产就绪。
