"""RAG 第三节：命中后补取相邻片段（离线模拟，不执行真实检索）。

expand_neighbors() 已完成，可运行示例并查看筛选顺序。
运行：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.neighbor_expansion
"""

from agent_learning.module_08_rag.document_chunking import load_documents
from agent_learning.module_08_rag.overlapping_chunking import build_overlapping_chunks


def expand_neighbors(
    chunks: list[dict], hit_chunk_id: str, window: int = 1
) -> list[dict]:
    """返回同一文档中，命中片段及其前后 window 段，按原文顺序排列。

    window=0：只返回命中片段。
    window=1：返回前一段、命中段、后一段；边界处只返回实际存在的段。
    chunks 可以乱序，但约定来自同一套切分结果，chunk_id 唯一。
    不修改输入；负 window 抛 ValueError；找不到命中 ID 抛 ValueError。
    本节只处理一个命中，不涉及多个命中合并、重叠文本去重或 Token 预算。
    """
    if window < 0:
        raise ValueError("window 不能为负数")

    # 已完成：根据 ID 找到模拟检索命中的片段。
    hit = None
    for chunk in chunks:
        if chunk["chunk_id"] == hit_chunk_id:
            hit = chunk
            break
    if hit is None:
        raise ValueError(f"找不到命中片段：{hit_chunk_id}")

    document_id = hit["document_id"]
    hit_index = hit["metadata"]["chunk_index"]
    selected = []

    for chunk in chunks:
        # 1. 先限定同一篇文档，避免混入其他英雄的片段。
        if chunk["document_id"] != document_id:
            continue

        # 2. 用原文片段序号判断范围，不使用 chunks 列表中的位置。
        chunk_index = chunk["metadata"]["chunk_index"]
        if hit_index - window <= chunk_index <= hit_index + window:
            # 3. 保存完整字典，保留正文、片段编号和来源信息。
            selected.append(chunk)

    # 已完成：sorted 返回新列表；lambda 指定按每个片段的序号排序。
    return sorted(selected, key=lambda chunk: chunk["metadata"]["chunk_index"])


def make_demo_chunks() -> list[dict]:
    """已完成：人为构造并打乱顺序的测试片段，文本不代表英雄背景事实。"""
    rows = [
        ("yasuo", 2, "这里是接在命中段后面的解释。"),
        ("ahri", 1, "这是另一篇文档，序号相同也不能混入。"),
        ("yasuo", 0, "这里是前面的背景信息。"),
        ("yasuo", 3, "这里是更后面的补充。"),
        ("yasuo", 1, "这里模拟检索命中，完整解释在后一段。"),
    ]
    return [
        {
            "chunk_id": f"{document_id}_{index:03d}",
            "document_id": document_id,
            "text": text,
            "metadata": {"chunk_index": index, "source_file": "demo_only"},
        }
        for document_id, index, text in rows
    ]


def main() -> None:
    chunks = make_demo_chunks()
    # 这个 ID 是手动指定的，模拟检索已经返回了一个命中。
    hit_chunk_id = "yasuo_001"
    print("模拟命中：", hit_chunk_id)
    expanded = expand_neighbors(chunks, hit_chunk_id, window=1)
    for chunk in expanded:
        print(chunk["chunk_id"], chunk["text"])

    cases = [
        ("前后各一段且不跨文档", "yasuo_001", 1, [0, 1, 2]),
        ("只取命中段", "yasuo_001", 0, [1]),
        ("命中第一段", "yasuo_000", 1, [0, 1]),
        ("命中最后一段", "yasuo_003", 1, [2, 3]),
        ("窗口大于文档长度", "yasuo_001", 10, [0, 1, 2, 3]),
        ("只有一段的文档", "ahri_001", 1, [1]),
    ]
    for name, hit_id, window, expected in cases:
        actual = expand_neighbors(chunks, hit_id, window)
        assert [c["metadata"]["chunk_index"] for c in actual] == expected, name
        hit = next(c for c in chunks if c["chunk_id"] == hit_id)
        assert all(c["document_id"] == hit["document_id"] for c in actual), name
        print(f"通过：{name}")
    assert chunks == make_demo_chunks(), "不能修改输入片段或原列表顺序"

    for data, hit_id, window in [
        (chunks, "yasuo_001", -1),
        (chunks, "missing", 1),
        ([], "yasuo_001", 1),
    ]:
        try:
            expand_neighbors(data, hit_id, window)
        except ValueError:
            pass
        else:
            raise AssertionError("负窗口或找不到命中 ID 时应抛出 ValueError")
    print("通过：非法参数和缺失命中检查")

    # 沿用上一节的真实资料切分，只打印编号，不请求模型。
    real_chunks = build_overlapping_chunks(load_documents(), 300, 50)
    real_hit = real_chunks[0]["chunk_id"]
    neighbors = expand_neighbors(real_chunks, real_hit, window=1)
    print("资料演示，手动选定命中：", real_hit)
    print("扩展后的片段：", [c["chunk_id"] for c in neighbors])


if __name__ == "__main__":
    main()
