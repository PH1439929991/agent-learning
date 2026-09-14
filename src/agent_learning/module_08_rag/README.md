# 模块八：RAG（检索增强生成）

RAG 的基本流程是：先从资料中检索相关片段，再把片段和用户问题一起交给模型生成答案。

本模块沿用英雄资料，逐步学习：文档整理与切片、Embedding、相似度检索、构造带资料的 Prompt，以及来源引用和检索效果测试。

## 第一节：读取文档与切片

已完成 [document_chunking.py](document_chunking.py) 中的 `split_text()`，保留本节用于对比。当前练习是下方第五节的真实 Embedding 接口调用。

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

## 第五节：调用真实 Embedding 模型（当前练习）

打开 [real_embeddings.py](real_embeddings.py)，只实现 `embed_text()` 两个 TODO：调用 `client.embeddings.create`，然后返回 `response.data[0].embedding`。独立客户端配置、相似度计算与排序展示已写好。API 字段按 [OpenAI 官方 Python 文档](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create) 核对。

输入用 `input=text`，不是聊天的 `messages`，也不需要 system prompt。输出是数字列表，不是回答文字。本节先比较一个问题和两条候选短文本，暂不编码整个资料库；后面再批量给 chunks 加入 embedding、接入检索。

在本地 `src/agent_learning/.env` 补充 `EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL`，填写方式见 [.env.example](../.env.example)。已有 `DEEPSEEK_*` 保持不变；聊天配置不能证明服务提供 Embedding 接口。三项配置必须来自匹配的服务商，密钥不要发到聊天中。当前尚未验证你的 Embedding 服务及账户可用性；如未选择服务，先确认服务商再填写，不能只把聊天模型名复制过来。

默认运行只显示说明，不发请求：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.real_embeddings
```

完成 TODO、填好配置后，显式允许真实调用：

```bash
PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.real_embeddings --live
```

每次正常完成会向配置的服务发送文件中列出的三句短文本，共 3 次请求，可能计费；失败时停止，不自动重试。本节复用已安装的 SDK，无新增依赖。不读取真实配置执行远程测试，不将向量写入文件；反复运行 live 会重新请求。默认说明模式通过不等于 TODO 或远程服务已验证。
