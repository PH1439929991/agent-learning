"""RAG 第七节：把向量索引保存到 JSON，下次直接读取。

只完成 save_index() 和 load_index() 的 TODO。默认运行不发请求。
--build --live：编码全部资料并保存；--query "问题" --live：只编码问题。
缓存只存模型、服务地址、资料指纹与片段向量，不存 API Key。
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from agent_learning.module_08_rag.document_chunking import load_documents
from agent_learning.module_08_rag.overlapping_chunking import build_overlapping_chunks
from agent_learning.module_08_rag.real_embeddings import create_embedding_client, embed_text
from agent_learning.module_08_rag.top_k_retrieval import build_vector_index, search_top_k


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INDEX_PATH = PROJECT_ROOT / "work" / "rag_index.json"


def save_index(payload: dict, path: Path) -> None:
    """练习：把整个索引字典保存到 UTF-8 JSON 文件。

    使用 x 模式：仅创建新文件；文件已存在就报 FileExistsError，不覆盖旧索引。
    json.dump 写入文件，json.dumps 只是返回字符串，注意两者区别。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # TODO 1：用 with path.open("x", encoding="utf-8") as file: 打开文件。
    # TODO 2：在 with 内用 json.dump(payload, file, ensure_ascii=False, indent=2,
    # allow_nan=False) 保存整个字典。无需 return。
    with path.open("x", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, allow_nan=False)


def load_index(path: Path) -> dict:
    """练习：读取 JSON，恢复成 Python 字典，不调用模型。

    文件不存在时保留 FileNotFoundError；内容损坏时保留 JSONDecodeError。
    不自动重新建库，避免在查询时意外发送全部资料并计费。
    """
    # TODO 1：用 with path.open("r", encoding="utf-8") as file: 打开文件。
    # TODO 2：返回 json.load(file)，得到字典，不是 JSON 字符串。
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def source_fingerprint(chunks: list[dict]) -> str:
    """已完成：给当前切分结果计算指纹；正文、来源、边界变化会改变指纹。"""
    text = json.dumps(chunks, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_index(payload: dict, model: str, base_url: str, chunks: list[dict]) -> None:
    """已完成：拒绝格式不符、过期或属于其他模型/服务的缓存。"""
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("索引格式不支持，请重新建库")
    if payload.get("model") != model or payload.get("base_url") != base_url:
        raise ValueError("索引模型或服务与当前配置不一致，请重新建库")
    if payload.get("source_hash") != source_fingerprint(chunks):
        raise ValueError("资料或切分方式已变化，请重新建库")
    stored = payload.get("chunks")
    if not isinstance(stored, list) or not stored or len(stored) != len(chunks):
        raise ValueError("索引片段数量不正确")
    dimension = None
    for original, saved in zip(chunks, stored):
        if not isinstance(saved, dict) or {k: v for k, v in saved.items() if k != "embedding"} != original:
            raise ValueError("索引正文或元数据与当前资料不一致")
        vector = saved.get("embedding")
        if not isinstance(vector, list) or not vector:
            raise ValueError("索引缺少向量")
        if not all(type(v) in (int, float) and math.isfinite(v) for v in vector) or not any(vector):
            raise ValueError("索引向量必须是非零且有限的数值列表")
        if dimension is not None and len(vector) != dimension:
            raise ValueError("索引向量维度不一致")
        dimension = len(vector)


def main() -> None:
    parser = argparse.ArgumentParser(description="索引保存与复用练习")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--build", action="store_true", help="生成资料向量并保存索引")
    mode.add_argument("--query", help="读取索引并检索这个问题")
    parser.add_argument("--live", action="store_true", help="允许真实 Embedding 请求")
    parser.add_argument("--index-file", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if args.top_k < 1 or (args.query is not None and not args.query.strip()):
        parser.error("top-k 必须为正整数，query 不能为空")
    if not args.live or (not args.build and args.query is None):
        print("完成保存、读取 TODO 并通过离线测试后：")
        print("建库：--build --live（发送所有资料片段，可能计费）")
        print("查询：--query '亚索的背景故事' --live（仅发送问题，正常完成 1 次请求）")
        print("索引默认保存到 work/rag_index.json，不自动覆盖或自动重建。")
        return

    # 先读文件/检查目标，再创建客户端。缓存不存在或已存在时不会付费建库。
    if args.build:
        if args.index_file.exists():
            raise FileExistsError("索引已存在；查询直接用 --query，重建请用 --index-file 指定新文件")
        payload = None
    else:
        payload = load_index(args.index_file)
    chunks = build_overlapping_chunks(load_documents(), 300, 50)
    if not chunks:
        raise ValueError("没有可用资料")
    client, model = create_embedding_client()
    try:
        base_url = str(client.base_url)
        if args.build:
            print(f"将发送 {len(chunks)} 个片段生成向量；不生成问题向量。", flush=True)
            index = build_vector_index(client, model, chunks)
            payload = {"version": 1, "model": model, "base_url": base_url,
                       "source_hash": source_fingerprint(chunks), "chunks": index}
            validate_index(payload, model, base_url, chunks)
            save_index(payload, args.index_file)
            print("已保存：", args.index_file)
        else:
            # 在发送问题之前确认缓存仍可用，不相符时直接报错，不自动重建。
            validate_index(payload, model, base_url, chunks)
            query_vector = embed_text(client, model, args.query)
            hits = search_top_k(query_vector, payload["chunks"], args.top_k)
            for hit in hits:
                chunk = hit["chunk"]
                print(f"\n{chunk['chunk_id']} | 相似度 {hit['score']:.4f}")
                print(chunk["text"])
            print("本次读取已有资料向量，只为问题请求了 1 次 Embedding。")
    finally:
        client.close()


if __name__ == "__main__":
    main()
