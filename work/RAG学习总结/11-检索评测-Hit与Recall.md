# 第十一节：检索评测——Hit@K 与 Recall@K

学习日期：2026-09-17。第十节按你反馈已在家完成，本机旧实现尚未同步，本节不重复修改它。

## 1. 这一节要解决什么问题

之前检查：“模型引用的 [1] 这个编号存不存在？”

现在检查：“该找到的资料，检索器到底有没有找到？”

这两个检查不是一回事。即使引用编号有效，检索到的资料也可能不相关。本节只评测检索结果，不生成答案、不调用模型、不产生 API 费用。

## 2. 先准备一份有标准答案的资料

用虚构角色做演示，避免依赖未经核验的英雄背景：

| chunk_id | 正文 |
| --- | --- |
| demo_000 | 练习角色住在示例地区。 |
| demo_001 | 练习角色喜欢阅读。 |
| demo_002 | 另一位角色喜欢游泳。 |
| demo_003 | 示例地区有一座图书馆。 |

用户问：“练习角色住在哪里，喜欢做什么？”

人工阅读以上资料，标出两个相关片段：demo_000 和 demo_001。

```python
case = {
    "query": "练习角色住在哪里，喜欢做什么？",
    "expected_chunk_ids": ["demo_000", "demo_001"],
}
```

expected_chunk_ids 是事先标注的相关片段，不是模型生成的回答，也不是检索器自己返回的结果。信息检索评测需要问题、资料集合和相关性标注，参见 [Stanford《Introduction to Information Retrieval》](https://nlp.stanford.edu/IR-book/html/htmledition/information-retrieval-system-evaluation-1.html)。

本节用片段 ID 表示相关性。真实资料如果有多个等价或重叠片段，也应按一致标准标注；漏标相关片段会影响指标。改了资料或切片方式后，要检查原来的 ID 和标注是否仍然有效。

## 3. 再取得检索结果

假设检索器按相似度从高到低返回：

```python
retrieved_ids = ["demo_002", "demo_000", "demo_003", "demo_001"]
k = 3
```

这里只是手写排名，用来学习指标，不代表真实模型表现。

先取前 K 条：

```python
top_k_ids = retrieved_ids[:k]
# ["demo_002", "demo_000", "demo_003"]
```

注意：demo_001 虽然在完整结果中，但排在第四，不算本次 Top-3 命中。

在真实项目中，hits 是 search_top_k 的返回值，可以这样提取 ID：

```python
retrieved_ids = [hit["chunk"]["chunk_id"] for hit in hits]
```

这里比较的是稳定的 chunk_id，不是回答中的 [1]、[2]。引用编号是当次消息里的位置，换一个排名它就可能变化。

## 4. Hit@K：有没有至少找到一条

本节约定：对单个问题，Hit@K 返回布尔值。

- 前 K 条中至少有一个预期相关片段：True。
- 一个都没有：False。

上述例子命中了 demo_000，所以 Hit@3=True。

但问题同时问居住地和爱好，只找到一段还不够。Hit@K 只表示“至少命中一条”，不表示问题已经可以完整回答。

## 5. Recall@K：该找的资料找回了多少

召回率的分母是全部相关项数量，分子是找回的相关项数量；限制到前 K 条，就得到本节的 Recall@K。参见 [召回率定义](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)与 [Top-K 排名评测](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)。

```text
Recall@K = 前 K 条命中的不同相关片段数 / 预期相关片段总数
```

上述例子：

```text
预期相关：demo_000、demo_001，共 2 段
实际命中：demo_000，共 1 段
Recall@3 = 1 / 2 = 0.5
```

分母不是 K，也不是全库片段总数。

## 6. 用同一份排名对比 K

预期相关片段始终为 demo_000、demo_001：

| K | 实际参与评测的前 K 条 | 命中数 | Hit@K | Recall@K |
| --- | --- | --- | --- | --- |
| 1 | demo_002 | 0 | False | 0.0 |
| 2 | demo_002、demo_000 | 1 | True | 0.5 |
| 3 | demo_002、demo_000、demo_003 | 1 | True | 0.5 |
| 4 | demo_002、demo_000、demo_003、demo_001 | 2 | True | 1.0 |

同一排名中增大 K，召回率不会降低，但不意味着最终回答一定更好：发给模型的资料可能更多、更杂，输入开销也会增加。

## 7. Python 中怎样比较

set 是集合，用来去重；& 表示取两个集合共同存在的元素。

```python
expected = {"demo_000", "demo_001"}
retrieved = {"demo_002", "demo_000", "demo_003"}
matched = expected & retrieved
# {"demo_000"}
```

集合不保证排名顺序，所以必须先在原列表中取前 K 条，再转换成集合，不能先转集合再选 Top-K。

如果同一个 ID 被返回两次，不应该算两次命中。本题先截取 K 个原始位置，再去重计数；重复项仍占用了排名位置，不用后面的片段补位。

例如预期 A、B，排名 A、A、B，K=2：只命中 A，Recall@2=0.5，而不是 1.0。

## 8. 你的练习

先阅读，再尝试填写下面的函数。此处是文档练习模板，尚未新建可执行 Python 文件。

```python
def evaluate_retrieval(
    expected_chunk_ids: list[str],
    retrieved_chunk_ids: list[str],
    k: int = 3,
) -> dict:
    if type(k) is not int or k < 1:
        raise ValueError("k 必须是正整数")
    if not expected_chunk_ids:
        raise ValueError("本题需要至少一个预期相关片段")

    # TODO 1：将 expected_chunk_ids 转为集合 expected。
    # 将 retrieved_chunk_ids 的前 k 条转为集合 retrieved。
    expected = set(expected_chunk_ids)
    retrieved = set(retrieved_chunk_ids[:k])
    # TODO 2：用集合交集得到 matched。
    matched = expected & retrieved

    # TODO 3：返回字典：
    # hit_at_k：是否有命中，用 bool(matched)。
    # recall_at_k：命中数除以去重后的预期相关片段数。
    # matched_ids：用 sorted(matched) 返回列表，方便稳定展示和测试。
    return{
        "hit_at_k": bool(matched),
        "recall_at_k": len(matched) / len(expected),
        "matched_ids": sorted(matched),
    }
```

函数只负责算指标，不读取 JSON、不重新检索、不生成向量。

## 9. 你可以手算这些 case

下表中的 A、B、C 是简写片段 ID。

| 预期片段 | 检索排名 | K | Hit@K | Recall@K |
| --- | --- | --- | --- | --- |
| A、B | C、A、B | 2 | True | 0.5 |
| A、B | C、A、B | 3 | True | 1.0 |
| A | C、B | 2 | False | 0.0 |
| A、B | 空列表 | 3 | False | 0.0 |
| A、B | A、A、B | 2 | True | 0.5 |
| A、B | A | 5 | True | 0.5 |

另外两类参数检查：K=0 或 True 应报错；预期相关片段为空也应报错。

为什么空预期不直接记为 0 分？因为可能是资料本来没有答案，也可能是还没标注。本题不能区分，而且召回率会出现分母为零。这里明确拒绝，另用“无答案问题”的拒答评测检查，不能把它混进普通召回率。

## 10. 多个问题怎样汇总

本节把单题指标与整组指标分开命名，避免混淆。

假设三个有相关资料的问题，单题 Hit@3 为 True、False、True，Recall@3 为 0.5、0.0、1.0：

```text
Hit rate@3 = 命中的问题数 / 问题数 = 2 / 3，约 66.7%
Mean Recall@3 = 单题召回率的平均值 = (0.5 + 0 + 1.0) / 3 = 0.5
```

这里每道题权重相同；先不用扩展到其他平均方式。不同工具可能使用不同指标名称，要先确认定义。

## 11. 学完应该能解释什么

1. Hit@K=True 为什么还可能没有找全资料？
2. Recall@K 的分母为什么不是 K？
3. 为什么不能拿检索器返回的结果作为 expected_chunk_ids？
4. 为什么要先切前 K 条，再用 set 去重？
5. 找对资料与回答正确为什么是两回事？

本节只搭建检索评测的概念与计算练习。真实检索好坏要等接入固定标注用例后再测，不能把手写 case 的通过率当成真实检索效果。
