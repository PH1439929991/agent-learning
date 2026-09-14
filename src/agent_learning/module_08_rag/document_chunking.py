"""RAG 第一节：读取英雄资料，整理文档，按字符数切片。

本节不调用模型、不生成向量。请完成 split_text() 中的三个 TODO。
运行：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.document_chunking
"""

import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "champions.json"


def load_documents(data_path: Path = DATA_PATH) -> list[dict]:
    """已完成：每位英雄转换成一篇文档，并保留来源信息。"""
    with data_path.open("r", encoding="utf-8") as file:
        champions = json.load(file)

    documents = []
    for champion_id, champion in champions.items():
        lines = [
            f"英雄：{champion['name_cn']}",
            f"称号：{champion.get('title', '')}",
            f"地区：{champion.get('region', '')}",
            f"简介：{champion.get('summary', '')}",
        ]
        for event in champion.get("key_events", []):
            lines.append(f"事件：{event['event']}。{event['description']}")
        for person in champion.get("related_characters", []):
            lines.append(
                f"相关人物：{person['name']}（{person['relationship']}）。"
                f"{person['description']}"
            )

        documents.append({
            "document_id": champion_id,
            "text": "\n".join(lines),
            "metadata": {
                "champion_name": champion["name_cn"],
                "region": champion.get("region", ""),
                "source_file": data_path.name,
                "source_url": champion.get("source_url", ""),
            },
        })
    return documents


def split_text(text: str, chunk_size: int = 300) -> list[str]:
    """练习：每 chunk_size 个字符切成一段，最后一段可以较短。

    示例：split_text("ABCDEFGHIJ", 4) 应返回 ["ABCD", "EFGH", "IJ"]。
    空字符串返回 []。保留原文的空格和换行，不做 strip()。
    chunk_size 的单位是 Python 字符数，不是 Token 数。
    """
    if chunk_size < 1:
        raise ValueError("chunk_size 必须大于等于 1")

    chunks = []
    # 提示：for start in range(0, len(text), chunk_size):
    for start in range(0, len(text), chunk_size):
        text_part = text[start:start + chunk_size]
        chunks.append(text_part)
    return chunks


def build_chunks(documents: list[dict], chunk_size: int = 300) -> list[dict]:
    """已完成：分别切每篇文档，给每一段附上编号和来源。"""
    chunks = []
    for document in documents:
        parts = split_text(document["text"], chunk_size)
        for chunk_index, part in enumerate(parts):
            chunks.append({
                "chunk_id": f"{document['document_id']}_{chunk_index:03d}",
                "document_id": document["document_id"],
                "text": part,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": chunk_index,
                    "start_char": chunk_index * chunk_size,
                },
            })
    return chunks


def main() -> None:
    print("小例子：", split_text("ABCDEFGHIJ", chunk_size=4))
    documents = load_documents()
    chunks = build_chunks(documents, chunk_size=300)
    print(f"文档数量：{len(documents)}，片段数量：{len(chunks)}")
    for chunk in chunks[:2]:
        print(json.dumps(chunk, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
