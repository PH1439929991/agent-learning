# 模块八：RAG（检索增强生成）

当前统一入口：[第八章总览与顺序关联](../../../work/RAG学习总结/00-第八章总览与顺序关联.md)。第 1～16 节的作用、概念图、已验证边界与第 17 节综合题都集中在那里；下文前十节保留为历史练习说明。第十节你反馈在家完成，本机旧文件尚未同步。

2026-09-17 更新：第十七节主流程与三类真实样例已验收，见 [完整 RAG 与真实验收](../../../work/RAG学习总结/17-完整RAG与真实验收.md)。入口为 `rag_live_acceptance.py`，默认不联网，只有 `--live` 才请求真实服务。下一节为 Agent 工具集成。

第十八节已完成：[检索工具与真实问答记录](../../../work/RAG学习总结/18-把检索接成Agent工具.md)。`rag_search_tool.py` 的 13 个测试通过，`rag_agent_live.py` 的 14 个测试通过，并完成一次真实工具问答；入口默认不联网，需显式 --live。第八章基础练习收尾。

RAG 的基本流程是：先从资料中检索相关片段，再把片段和用户问题一起交给模型生成答案。

本模块沿用英雄资料，逐步学习：文档整理与切片、Embedding、相似度检索、构造带资料的 Prompt，以及来源引用和检索效果测试。

## 第一节：读取文档与切片

已完成 [document_chunking.py](document_chunking.py) 中的 `split_text()`，保留本节用于对比。当前练习是下方第十节的生成与引用检查集成。

已写好的 `load_documents()` 读取 `champions.json`，把每位英雄的简介、事件和人物关系拼成一篇文本。`build_chunks()` 会调用你的切片函数，把片段包装成带元数据的字典。

本节运行顺序：

```text
champions.json
→ load_documents()：一位英雄一篇文档
→ split_text()：一篇文档切成多段
→ build_chunks()：给各段附上英雄名、片段编号和来源
```

`text` 是供后续检索和生成使用的正文；`metadata` 是描述正文的信息，例如英雄名、地区、来源链接。即使某一段正文没有英雄名字，也能通过 metadata 找回它属于谁。

片段编号如 `yasuo_000`，表示亚索文档的第 0 段。不同英雄分别切片，不会把上一位英雄的结尾和下一位的开头混到一起。这些编号用于本次资料版本；修改原文或切片参数后，需要重新生成片段和后续索引。

## 你的三个 TODO

1. 使用 `range(0, len(text), chunk_size)` 遍历每段起点。
2. 在循环内用 `text[start:start + chunk_size]` 取片段并追加到列表。
3. 循环结束后返回列表。

完成后删除函数中的 `raise NotImplementedError(...)`。未完成时运行会主动提示待实现，属于练习预期。

例如 `text="ABCDEFGHIJ"`、`chunk_size=4`：

| start | 切片表达式 | 内容 |
| --- | --- | --- |
| 0 | `text[0:4]` | `ABCD` |
| 4 | `text[4:8]` | `EFGH` |
| 8 | `text[8:12]` | `IJ` |

Python 切片包含起点、不包含终点；终点超过字符串长度时会取到结尾。

在项目根目录运行：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.document_chunking
```

完成后的第一行应输出 `['ABCD', 'EFGH', 'IJ']`，后面显示英雄文档数、片段数和前两个片段。

检查点：空文本返回 `[]`；最后一段可以少于 chunk_size；整除时不多生成空段；`''.join(parts)` 能恢复原文。

## 这一版的范围

当前 chunk_size 按 Python 字符数计算，空格和换行也占长度，不是 Token 数。固定长度切片可能切断一句话，后面再学习段落边界与重叠片段。本节不调用模型，不生成向量，也不把片段写回原 JSON。

现有 JSON 是学习资料，尚未逐条核实。保留 source_url 只表示保留原文件标注的来源，不代表内容已核验。RAG 不能自动修正资料中的错误；正式用于背景故事问答前，需要核查原文和来源。

## 第二节：重叠切分（已完成）

打开 [overlapping_chunking.py](overlapping_chunking.py)，只实现 `split_text_with_overlap()` 的四个 TODO。第一节代码不用改。

固定长度切分可能把相关信息分到两段。让相邻片段重复一部分内容，可以缓解边界信息不完整的问题，但不能保证检索一定成功。

- `chunk_size`：每段最多多少个字符。
- `overlap`：相邻片段重复多少个字符，必须满足 `0 <= overlap < chunk_size`。
- `step = chunk_size - overlap`：每次起点前进多少个字符。

例如 `ABCDEFGHIJ`，每段 4 个字符，重叠 1 个字符：起点为 0、3、6，结果应为 `['ABCD', 'DEFG', 'GHIJ']`。本段一旦覆盖原文结尾，就结束循环，不再生成只有 `J` 的重复尾段。

四个 TODO：计算步长、循环取片段并追加、覆盖结尾后 break、循环外 return。参数校验、元数据包装、运行示例和断言已经准备好。

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.overlapping_chunking
```

未实现时会抛出 `NotImplementedError`；完成后会比较两种切分，执行边界检查，再打印英雄资料片段。本节仍不调用模型或网络，不写回原始资料。

注意两个变化：

1. 片段起点变为 `chunk_index * step`，不再是 `chunk_index * chunk_size`，包装函数已经修改。
2. 有重复内容后，不能直接用 `''.join(parts)` 还原原文；否则重叠区域也会重复。

重叠会增加存储和后续处理的文本量，不是越大越好。当前仅比较两种切分策略；它们的片段编号可能相同，后续建立索引时应选定一种策略，不要直接混用两套结果。

## 第三节：命中后补取相邻片段（已完成）

打开 [neighbor_expansion.py](neighbor_expansion.py)，只实现 `expand_neighbors()` 的三个 TODO。前两节代码不用改。

本节暂时手动指定命中 ID，模拟“检索已经找到某一段”，不执行真实搜索，不调用模型。后面再学习 Embedding 和相似度检索，把真实检索结果接到这里。

目标：命中 `yasuo_001`，`window=1` 时，返回同一文档的 `yasuo_000`、`yasuo_001`、`yasuo_002`。先按 `document_id` 限定文档，再按 `chunk_index` 筛选邻居，最后按原文顺序排列。`window=0` 只保留命中段；到了文档头尾，不存在的邻居不用补。

已准备好参数校验、命中查找、排序和测试。你来完成：遍历并排除其他文档、判断片段序号范围、追加完整片段字典。测试数据故意打乱顺序，不能直接按列表下标截取邻居。

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.neighbor_expansion
```

未完成时会抛出 `NotImplementedError`。完成后运行模拟命中展示、边界断言，再用上一节的英雄片段演示扩展。

本节只扩展单个命中，保留各片段及来源，不拼成最终 Prompt。多个命中之间的去重、重叠正文合并和总上下文预算留到后面；窗口越大不一定越好，也可能带入无关信息。

## 第四节：Embedding 概念与向量相似度（已完成）

Embedding 模型把文本编码为一组数字，即向量。文本检索通常先编码资料片段，再编码问题，比较向量并选取相关片段。它不是把字符转换成编号，也不是生成聊天回答。

打开 [embedding_basics.py](embedding_basics.py)，只实现 `cosine_similarity()` 的两个 TODO：计算对应位置乘积之和（点积），再除以两个向量数学长度的乘积。长度计算、校验、排序和相邻片段扩展已经写好。

余弦相似度比较方向，数学范围为 -1 到 1；同方向为 1、垂直为 0、反方向为 -1。它不是正确率，也不是“回答正确的概率”。真实语义相关性取决于模型和任务，不要给向量每个维度随意命名为某种语义。

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.embedding_basics
```

本节明确使用手工演示向量，只学习“打分 → 排序 → 命中 → 补取邻居”，不具备真实文本语义检索能力，不调用模型、不增加依赖。未完成时抛 `NotImplementedError`；完成后执行数学用例与排序演示。

下一步再接真实 Embedding 模型生成这些数字。问题和资料必须使用兼容的同一套模型/编码配置，不能仅凭维度相同就混用不同模型的向量。存储结构暂时是在 chunk 上增加 `embedding` 列表，仍不是数据库。

## 第五节：调用真实 Embedding 模型（已完成）

2026-09-15 已用硅基流动 `Qwen/Qwen3-Embedding-0.6B` 完成三次真实请求，向量为 1024 维。本次“亚索资料”和“意大利面”得分分别约为 0.8329 和 0.2718；仅记录本次观察，不作为固定预期分数。

打开 [real_embeddings.py](real_embeddings.py)，只实现 `embed_text()` 两个 TODO：调用 `client.embeddings.create`，然后返回 `response.data[0].embedding`。独立客户端配置、相似度计算与排序展示已写好。API 字段按 [OpenAI 官方 Python 文档](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create) 核对。

输入用 `input=text`，不是聊天的 `messages`，也不需要 system prompt。输出是数字列表，不是回答文字。本节先比较一个问题和两条候选短文本，暂不编码整个资料库；后面再批量给 chunks 加入 embedding、接入检索。

在本地 `src/agent_learning/.env` 补充 `EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL`，填写方式见 [.env.example](../.env.example)。已有 `DEEPSEEK_*` 保持不变；聊天配置不能证明服务提供 Embedding 接口。三项配置必须来自匹配的服务商，密钥不要发到聊天中。新电脑需要自行配置并确认账户可用性，不能只把聊天模型名复制过来。

默认运行只显示说明，不发请求：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.real_embeddings
```

完成 TODO、填好配置后，显式允许真实调用：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.real_embeddings --live
```

每次正常完成会向配置的服务发送文件中列出的三句短文本，共 3 次请求，可能计费；失败时停止，不自动重试。本节复用已安装的 SDK，无新增依赖。不将向量写入文件；反复运行 live 会重新请求。默认说明模式通过不等于 TODO 或远程服务已验证。

## 第六节：英雄资料 Top-K 检索（代码已完成）

打开 [top_k_retrieval.py](top_k_retrieval.py)，只完成 `search_top_k()` 的两个 TODO：调用 `rank_chunks` 打分排序，再截取前 `top_k` 条。默认返回每条结果的完整 `chunk` 和 `score`，不只是 ID。

`build_vector_index()` 已完成：对每个 chunk 的 text 调用上一节的 `embed_text()`，保存为 `{**chunk, "embedding": vector}`。这里的 index 是内存列表，不是向量数据库。在同一次运行中，准备一次资料向量后可以复用；当前命令每次重启都会重建，尚未做文件缓存或批量请求。

整体顺序：读取资料并切分 → 逐段编码建立 index → 编码 query → 本地打分排序 → 返回前 K 段。问题和片段使用相同的模型配置。本节先不补取邻居、不生成最终答案。

- `top_k=3`：全库相似度最高的 3 段，可能来自不同英雄；不是 3 位英雄。
- `window=1`：给某个命中段补取同文档前后各 1 段，是后续独立步骤。
- 空索引返回空列表；K 大于片段数量时返回全部；K 必须为正整数。
- 最高分不保证相关，来源链接不保证资料真实；后面再学习阈值、去重、上下文预算与资料核验。

先运行离线测试（不读密钥、不请求模型）：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_top_k_retrieval.py -q
```

TODO 未完成时，3 个核心检索用例会因 `NotImplementedError` 失败，这是预期的待完成练习；另外 6 个边界/配套用例可以运行。测试覆盖 K=1、2、超过总数、排序、保留完整记录、不修改输入、空索引、非法 K 和建索引。

完成并通过测试后，可显式发起真实请求：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.top_k_retrieval --live --query "我想了解亚索的背景故事。" --top-k 3
```

与第五节不同，这会发送所有英雄资料片段及问题。当前资料为 14 段，正常完成共 15 次 Embedding 请求，可能计费；以实际运行打印的数量为准。未带 `--live` 时只显示说明，不发请求。真实检索已通过第七节的缓存查询验证；已有索引请用第七节查询命令，不必反复重新编码资料。

## 第七节：索引保存与复用（已完成）

打开 [index_persistence.py](index_persistence.py)，实现 `save_index()` 和 `load_index()`。本节不新增模型接口，复用第五、六节函数。

你来实现两个文件操作：

1. 保存：用 `with path.open("x", encoding="utf-8") as file:`，在内部用 `json.dump(payload, file, ensure_ascii=False, indent=2, allow_nan=False)` 写入。`x` 只创建新文件，不覆盖旧文件。
2. 读取：用 `with path.open("r", encoding="utf-8") as file:`，返回 `json.load(file)` 恢复 Python 字典。

`dump` 写文件，`dumps` 返回字符串；`load` 读文件，`loads` 解析字符串。读取索引只是磁盘操作，不需要请求 Embedding。

文件不是只有向量，而是保存一个完整字典：

```python
{
    "version": 1,
    "model": "建库时的模型名称",
    "base_url": "建库时的服务根地址",
    "source_hash": "当前文档切分结果的指纹",
    "chunks": [
        # 每个片段的 ID、正文、metadata、embedding
    ],
}
```

不保存 API Key。`validate_index()` 已写好：拒绝不匹配的模型/服务、变动的资料或损坏的基本结构。指纹用于检测变化，不是加密，也不能证明来源可信；同名模型如果服务商更新了权重，仍可能需要主动重建。本节使用模型默认维度，后续增加编码参数时也要一起记录。

先运行离线测试，保存和读取未实现前 4 个文件操作用例会失败：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_index_persistence.py -q
```

完成后，第一次建库（当前 14 段即 14 次可能计费的请求，发送所有资料片段）：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.index_persistence --build --live
```

以后查询（读取已保存的资料向量，只发送用户问题，正常完成 1 次请求）：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.index_persistence --query "亚索的背景故事" --top-k 3 --live
```

默认文件是项目根目录的 `work/rag_index.json`，已加入 Git 忽略规则。2026-09-15 已经按请求真实建库：14 个片段，每段 1024 维；不带 `--live` 只显示说明。缺文件、缓存过期或模型不匹配时不会自动重建；已有文件不会覆盖，要重建可用 `--index-file work/rag_index_v2.json`，查询时也指定同一个路径。默认 JSON 写入并非原子事务，若中途失败留下不完整文件，需要检查后换一个文件名重建。

这是小型内存索引的文件缓存，不是向量数据库。本节仍不生成最终回答，也不自动合并邻居或核验英雄资料事实。真实查询“亚索的背景故事”观察到 `yasuo_000`（0.6369）、`yasuo_001`（0.5245）、`sion_001`（0.4501）；本次只请求了一次问题 Embedding，没有重建或修改索引。分数是本次观察，不是固定预期；第三条也说明 Top-K 不保证每条都相关。

## 第八节：检索资料 → messages → 生成答案（离线测试已通过）

`build_rag_messages()` 已完成，10 个离线测试全部通过。真实模型回答尚未验证；以下保留练习说明供回顾。

打开 [rag_answering.py](rag_answering.py)，只实现 `build_rag_messages()` 的三个 TODO。前面各节不用改。

这一节补齐 RAG 的“生成”：读取已有索引，编码问题，检索 Top-K，组装 messages，再请求聊天模型。向量负责找资料；聊天模型收到的是资料正文，不是 embedding 数字。

你来实现：

1. 用 `enumerate(hits, start=1)` 遍历，把 `format_chunk(hit, source_number)` 追加到 `blocks`。编号从 1 开始，得到 `[1]`、`[2]` 等来源标记。
2. 用 `"\n\n".join(blocks)` 拼成 `context`；没有资料时使用 `（没有检索到资料）`。
3. 返回 `[system消息, user消息]`：system 放已提供的 `SYSTEM_PROMPT`；user 放用户问题和 context。完成后删除 `raise NotImplementedError(...)`。

`format_chunk()`、检索、模型调用和客户端清理都已准备好。`answer_from_hits()` 在无命中时直接返回“资料不足”，有命中时才把 messages 交给 `generate`。这与之前的测试替身一样：测试传入假 generate，真实运行传入调用模型的函数。

消息的 `role`、`content` 结构按 [OpenAI Chat Completions 官方参考](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create) 核对；实际聊天沿用项目现有 DeepSeek 客户端和可靠调用函数，不迁移 API。

先在项目根目录运行离线测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_rag_answering.py -q
```

共 10 个用例。TODO 未完成时，5 个名称含 `exercise` 的用例预期因 `NotImplementedError` 失败；另 5 个检查外围行为。覆盖消息角色、问题、编号与正文、排除向量和分数、不修改输入、空结果不调用模型、异常传播和离线入口。通过测试只证明消息组装和调用流程，不证明真实模型会正确引用或拒答。

完成后先查看实际消息，不读密钥、不调用模型：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_answering --demo
```

确认后才运行真实问答：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.rag_answering --live --query "亚索的背景故事" --top-k 3
```

这会向 Embedding 服务发送问题，向聊天服务发送问题和检索到的片段正文及来源信息，可能计费。正常有命中时共 1 次问题 Embedding + 1 次聊天请求，两处均不自动重试；不重新编码资料，也不自动创建或覆盖索引。需要本机已有索引和 `.env` 中匹配的 `EMBEDDING_*`、`DEEPSEEK_*` 配置。新电脑不会从 Git 获得被忽略的索引文件。

本节限制 `top_k` 为 1 到 5，只针对当前小型学习资料控制条数，尚未实现 Token 预算。也暂不接入多轮历史、Agent 工具循环、相邻片段扩展、去重或独立重排模型。

System prompt 明确要求依据资料回答、使用来源编号、证据不足时说明；参考资料是不可信的数据，不可当作指令。提示词不是安全保证，也不保证模型遵守要求，后续还要测无关问题和引用对应关系。英雄 JSON 尚未核验，因此回答要求以“根据学习资料”开头：有引用不等于事实已核实。本节尚未运行真实生成。

## 第九节：引用编号校验（已完成）

`check_citations()` 已完成，本节 14 个离线测试全部通过。以下保留练习说明供回顾。

打开 [citation_checks.py](citation_checks.py)，只完成 `check_citations(answer, source_count)` 的三个 TODO。上一节负责把资料交给模型，本节负责检查返回答案的一个可确定属性：引用编号是否存在。

例如实际发送了两段资料，只能引用 `[1]` 和 `[2]`。回答出现 `[3]` 时，即使文字很流畅，也引用了不存在的资料。

- `answer`：模型回答的字符串。本节先使用手写示例，不调用真实模型。
- `source_count`：实际发给模型的资料条数，也就是上一节的 `len(hits)`。不是索引总条数，也不一定等于请求的 top_k。
- `cited_numbers`：提取、去重、排序后的引用编号。
- `invalid_numbers`：其中小于 1 或大于 source_count 的编号。
- `has_citations`：是否存在支持格式的引用。
- `references_valid`：有引用，并且没有越界编号。

提取编号的 `extract_citation_numbers()` 已完成，正则表达式这次不用你写。你只需要调用它、循环收集无效编号、返回检查字典。完成后删除 `raise NotImplementedError(...)`。

例如 `answer="角色喜欢阅读。[1] 角色喜欢游泳。[3]"`，`source_count=2`：应得到 `cited_numbers=[1, 3]`、`invalid_numbers=[3]`、`has_citations=True`、`references_valid=False`。

项目根目录运行离线测试：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_citation_checks.py -q
```

共 14 个用例；未实现时 8 个核心用例因 NotImplementedError 失败，另外 6 个提取与参数校验用例通过。覆盖正常编号、重复编号、越界、部分越界、零编号、没有引用、零资料和非法参数。完成后查看六组演示：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.citation_checks
```

重要边界：

1. 编号存在，不代表该段正文支持回答。比如 `[1]` 的正文是“喜欢阅读”，回答却写“喜欢游泳。[1]”，编号检查仍会通过。语义依据需另外评估。
2. 没有引用也不一定错。“资料不足，无法回答”可以不带引用。因此 references_valid 不是总的回答质量判定。
3. 仅识别半角 `[1]`、`[2]` 等无前导零数字格式；不支持 `[1,2]`、`[来源1]`、`[01]`，也不识别引用在句子中的语义位置。
4. 本节不修改原答案、不自动删除错误引用、不重试模型，也尚未接入真实问答入口。下一节先连接生成与检查，再学习答案依据评测。

## 第十节：生成回答后附上引用报告（当前练习）

打开 [checked_rag_answer.py](checked_rag_answer.py)，实现 `answer_with_citation_check(query, hits, generate)`。本题只连接已有函数，不重写消息组装和编号提取，不新增模型接口。

三个 TODO：

1. 调用 `answer_from_hits(query, hits, generate)` 得到 `answer`。
2. 调用 `check_citations(answer, source_count=len(hits))` 得到 `citation_check`。
3. 返回 `{"answer": answer, "citation_check": citation_check}`，删除 NotImplementedError。

`generate` 是函数，接收 messages，返回回答字符串。本题的演示和测试传入假生成器；消息组装与引用检查仍使用你已完成的真实代码。此处 hits 全部发送，没有再次过滤，因此实际来源条数就是 len(hits)。以后若过滤或扩展资料，需要按最终发送的来源重新编号并计数。

无命中时，已有的 answer_from_hits 不调用生成器，而是返回“资料不足”；引用检查仍执行，报告没有引用。检查失败时也保留原回答，不自动删除错误编号、不重新请求生成；生成函数报错时保留异常，不伪装成成功回答。

在项目根目录运行：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_checked_rag_answer.py -q
```

共 6 个用例：正常引用、越界引用、无命中不生成、有命中但回答无引用、生成异常、空问题。还检查只调用一次生成器、发送了正确的 messages、不修改 hits。未实现前 6 项均会因 NotImplementedError 失败，这是练习预期。

写完后运行纯离线演示：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.checked_rag_answer
```

演示只提供一段资料，假回答故意引用 [2]。应看到原回答保留，报告 invalid_numbers=[2]、references_valid=False。本节没有修改第八节的 live 入口，没有读取索引或请求模型，也不自动判断回答真假或拒答合理性。
