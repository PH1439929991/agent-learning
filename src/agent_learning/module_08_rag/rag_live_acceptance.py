"""第十七节真实验收：换掉两个回调，复用已经完成的 run_rag。

默认只显示说明；--live 最多 3 次问题向量请求 + 3 次聊天请求。
不重建索引、不自动重试；失败立即停止。字符预算不等于 Token 预算。
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

from agent_learning.module_08_rag.context_budget import demo_character_count
from agent_learning.module_08_rag.document_chunking import load_documents
from agent_learning.module_08_rag.index_persistence import (
    DEFAULT_INDEX_PATH, load_index, validate_index,
)
from agent_learning.module_08_rag.overlapping_chunking import build_overlapping_chunks
from agent_learning.module_08_rag.rag_pipeline import run_rag
from agent_learning.module_08_rag.real_embeddings import create_embedding_client, embed_text
from agent_learning.module_08_rag.top_k_retrieval import search_top_k


ACCEPTANCE_CASES = [
    {"case_id": "single_source", "query": "根据学习资料，璐璐的仙灵旅伴叫什么？"},
    {"case_id": "multiple_sources", "query": "根据学习资料，凯南和璐璐分别有什么能力？"},
    {"case_id": "insufficient_evidence",
     "query": "根据学习资料，璐璐第一次遇见皮克斯的确切公历日期（年月日）是什么？"},
]


def make_retrieve(client, model: str, index: list[dict], audit: list[dict]):
    """输入问题 → 仅计算问题向量 → 在已有资料向量中选 Top-K。"""
    def retrieve(query: str, k: int) -> list[dict]:
        # 请求前记录，因此失败的尝试也算一次，不是成功次数。
        event = {"kind": "embedding", "query": query, "status": "started"}
        audit.append(event)
        vector = embed_text(client, model, query)
        hits = search_top_k(vector, index, k)
        event.update(status="completed", dimension=len(vector), ranking=[
            {"chunk_id": hit["chunk"]["chunk_id"], "score": hit["score"]}
            for hit in hits
        ])
        return hits
    return retrieve


def make_generate(llm, audit: list[dict]):
    """输入预算筛选后的 messages → 一次真实聊天请求 → 答案字符串。

    DeepSeek 专用参数遵循其官方文档，不把 OpenAI 参数支持直接套过来。
    usage 是服务返回的实际 Token 统计，与本地字符计数分开记录。
    """
    request_client = llm.client.with_options(timeout=20.0, max_retries=0)

    def generate(messages: list[dict[str, str]]) -> str:
        event = {"kind": "chat", "status": "started"}
        audit.append(event)
        response = request_client.chat.completions.create(
            model=llm.model, messages=messages, temperature=llm.temperature,
            max_tokens=1024, extra_body={"thinking": {"type": "disabled"}},
        )
        event.update(
            status="responded", model=response.model,
            usage=response.usage.model_dump() if response.usage is not None else None,
        )
        if not response.choices:
            raise RuntimeError("模型未返回 choices")
        choice = response.choices[0]
        event["finish_reason"] = choice.finish_reason
        # 截断不能作为正常完成验收；停止，且不自动加预算再请求。
        if choice.finish_reason != "stop":
            raise RuntimeError("模型未正常结束，检查 finish_reason")
        if not isinstance(choice.message.content, str) or not choice.message.content.strip():
            raise RuntimeError("模型没有返回非空文本")
        event["status"] = "completed"
        return choice.message.content
    return generate


def run_cases(chunks, retrieve, generate):
    """逐题产生报告，方便一题完成就显示；异常不吞掉、不继续下一题。"""
    for case in ACCEPTANCE_CASES:
        started = perf_counter()
        result = run_rag(
            case["query"], chunks, retrieve, generate,
            input_budget=6000, count_messages=demo_character_count, top_k=3, window=1,
        )
        yield {**case, **result, "input_unit": "characters_not_tokens",
               "elapsed_seconds": round(perf_counter() - started, 3)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--index-file", type=Path, default=DEFAULT_INDEX_PATH)
    args = parser.parse_args()
    if not args.live:
        print("加 --live 执行三类验收：资料充足、多段资料、资料不足。")
        print("最多 3 次问题 Embedding + 3 次聊天；可能计费，不重建索引、不重试。")
        return

    # 先读本地缓存；缺失时直接失败，绝不偷偷发送全库重新编码。
    payload = load_index(args.index_file)
    chunks = build_overlapping_chunks(load_documents(), 300, 50)
    embedding_client, embedding_model = create_embedding_client()
    llm = None
    audit = []
    try:
        validate_index(payload, embedding_model, str(embedding_client.base_url), chunks)
        # 延迟导入：默认说明和离线测试不加载聊天密钥。
        from agent_learning.common.llm_client import LLMClient
        llm = LLMClient()
        retrieve = make_retrieve(embedding_client, embedding_model, payload["chunks"], audit)
        generate = make_generate(llm, audit)
        print("复用索引；输入上限 6000 字符（非 Token），单次输出上限 1024 Token。", flush=True)
        print("索引资料指纹：", payload["source_hash"], flush=True)
        for report in run_cases(chunks, retrieve, generate):
            # messages 仍保留在返回值里；终端只省略长正文，不省略来源/答案/检查。
            print(json.dumps({key: value for key, value in report.items() if key != "messages"},
                             ensure_ascii=False, indent=2), flush=True)
    finally:
        print("请求审计（每条记录为一次尝试；status 表示是否完成）：", flush=True)
        print(json.dumps(audit, ensure_ascii=False, indent=2), flush=True)
        embedding_client.close()
        if llm is not None:
            llm.client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # 不打印第三方原始错误正文或配置，避免无意暴露凭据。
        print(f"验收停止：{type(exc).__name__}，HTTP 状态={getattr(exc, 'status_code', None)}")
        raise SystemExit(1) from None
