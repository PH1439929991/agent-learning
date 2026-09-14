"""RAG 第二节：重叠切分。只需完成 split_text_with_overlap() 的 TODO。

运行（无需模型或网络）：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.overlapping_chunking
"""

import json

from agent_learning.module_08_rag.document_chunking import load_documents, split_text


def split_text_with_overlap(
    text: str, chunk_size: int = 300, overlap: int = 50
) -> list[str]:
    """按 Python 字符数切分，保留空格和换行。

    chunk_size：每段最多多少个字符。
    overlap：相邻片段重复多少个字符。
    step：下一段起点向前移动多少个字符，即 chunk_size - overlap。

    示例：ABCDEFGHIJ，chunk_size=4，overlap=1
    起点依次是 0、3、6，返回 ["ABCD", "DEFG", "GHIJ"]。
    最后一段已覆盖原文结尾时就停止，不再额外生成只有 "J" 的重复尾段。
    空字符串返回 []；overlap=0 时应与第一节的 split_text() 一致。
    """
    if chunk_size < 1:
        raise ValueError("chunk_size 必须大于等于 1")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")

    # 删除下面的占位异常，再完成四个 TODO。
    step = chunk_size - overlap

    chunks = []
    for start in range(0, len(text), step):
        if start + chunk_size >= len(text):
                start = text[start:]
                chunks.append(start)
                return chunks
        text_part = text[start:start + chunk_size]
        chunks.append(text_part)
    return chunks


def build_overlapping_chunks(
    documents: list[dict], chunk_size: int = 300, overlap: int = 50
) -> list[dict]:
    """已完成：分别切分英雄文档，保留来源和准确的字符起点。"""
    if chunk_size < 1:
        raise ValueError("chunk_size 必须大于等于 1")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")
    step = chunk_size - overlap
    chunks = []
    for document in documents:
        parts = split_text_with_overlap(document["text"], chunk_size, overlap)
        for chunk_index, part in enumerate(parts):
            chunks.append({
                "chunk_id": f"{document['document_id']}_{chunk_index:03d}",
                "document_id": document["document_id"],
                "text": part,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": chunk_index,
                    # 有重叠后不能再用 chunk_index * chunk_size。
                    "start_char": chunk_index * step,
                },
            })
    return chunks


def main() -> None:
    # 已完成：先比较效果，再检查边界，最后演示真实资料。
    text = "ABCDEFGHIJ"
    print("不重叠：", split_text(text, chunk_size=4))
    print("重叠 1 个字符：", split_text_with_overlap(text, 4, 1))

    cases = [
        ("常规重叠", text, 4, 1, ["ABCD", "DEFG", "GHIJ"]),
        ("不足一段", "ABC", 4, 1, ["ABC"]),
        ("刚好一段", "ABCD", 4, 1, ["ABCD"]),
        ("最后一段较短", "ABCDEFGH", 4, 1, ["ABCD", "DEFG", "GH"]),
        ("空字符串", "", 4, 1, []),
        ("不重叠", text, 4, 0, ["ABCD", "EFGH", "IJ"]),
        ("中文", "亚索来自艾欧尼亚", 4, 1, ["亚索来自", "自艾欧尼", "尼亚"]),
        ("保留空格换行", " A\nB ", 3, 1, [" A\n", "\nB "]),
        ("较大重叠", "ABCDE", 4, 3, ["ABCD", "BCDE"]),
    ]
    for name, value, size, overlap, expected in cases:
        actual = split_text_with_overlap(value, size, overlap)
        assert actual == expected, f"{name}：预期 {expected!r}，实际 {actual!r}"
        print(f"通过：{name}")

    for size, overlap in [(0, 0), (4, -1), (4, 4), (4, 5)]:
        try:
            split_text_with_overlap("ABC", size, overlap)
        except ValueError:
            pass
        else:
            raise AssertionError(f"应拒绝参数：chunk_size={size}, overlap={overlap}")
    print("通过：非法参数检查")

    documents = load_documents()
    chunks = build_overlapping_chunks(documents, chunk_size=300, overlap=50)
    print(f"文档数量：{len(documents)}，重叠片段数量：{len(chunks)}")
    for chunk in chunks[:2]:
        print(json.dumps(chunk, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
