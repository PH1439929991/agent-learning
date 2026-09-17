"""第十七节综合题：连接检索、扩展、预算、生成和引用检查。

先读 work/RAG学习总结/00-第八章总览与顺序关联.md。
只填写 run_rag 的三个 TODO。默认演示使用假检索和假生成，不调用模型。
"""

import json
from typing import Callable

from agent_learning.module_08_rag.citation_checks import check_citations
from agent_learning.module_08_rag.context_budget import demo_character_count, select_context
from agent_learning.module_08_rag.context_expansion import expand_context_chunks, make_example


def prioritize_hits(hits: list[dict], expanded: list[dict]) -> list[dict]:
    """已完成：先按检索排名放直接命中，再放扩展得到的其他片段。"""
    by_id = {chunk["chunk_id"]: chunk for chunk in expanded}
    ordered_ids = list(dict.fromkeys(
        [hit["chunk"]["chunk_id"] for hit in hits]
        + [chunk["chunk_id"] for chunk in expanded]
    ))
    return [by_id[chunk_id] for chunk_id in ordered_ids]


def finish_run(hits: list[dict], selection: dict, generate: Callable) -> dict:
    """已完成：只生成一次；无可用片段时本地说明，不请求生成器。

    status 描述执行路径，不评判回答真假、相关性或拒答是否合理。
    检查失败仍保留原回答；生成失败向上传播，不自动重试。
    """
    if not selection["selected_chunks"]:
        status = "no_retrieval" if not hits else "no_context"
        answer = ("本次没有检索到资料，无法据此回答。" if not hits
                  else "输入预算内没有可用资料片段，无法据此回答。")
    else:
        status = "generated"
        answer = generate(selection["messages"])
    return {
        "status": status,
        "answer": answer,
        "retrieved_ids": [hit["chunk"]["chunk_id"] for hit in hits],
        "source_ids": [chunk["chunk_id"] for chunk in selection["selected_chunks"]],
        "omitted_ids": [chunk["chunk_id"] for chunk in selection["omitted_chunks"]],
        "source_count": selection["source_count"],
        "messages": selection["messages"],
        "input_size": selection["input_size"],
        "input_budget": selection["input_budget"],
        "citation_check": check_citations(answer, selection["source_count"]),
    }


def run_rag(
    query: str, chunks: list[dict],
    retrieve: Callable[[str, int], list[dict]],
    generate: Callable[[list[dict[str, str]]], str],
    input_budget: int,
    count_messages: Callable[[list[dict[str, str]]], int],
    top_k: int = 3, window: int = 1,
) -> dict:
    """综合练习：只串联已有函数，不读取密钥、不自行创建模型客户端。

    chunks 与 retrieve 返回的片段须来自同一版本资料，适配器负责这一约束。
    count_messages 与 input_budget 使用相同单位，演示不是实际 Token 预算。
    """
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k 必须是正整数")
    if type(window) is not int or window < 0:
        raise ValueError("window 必须是非负整数")
    # 先检查基础消息预算与问题，避免明显非法输入进入真实检索适配器。
    select_context(query, [], input_budget, count_messages)
    ids = [chunk["chunk_id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("chunks 的 chunk_id 必须唯一")

    # TODO 1：hits = retrieve(query, top_k)。
    # 再调用 expand_context_chunks(chunks, hits, window)，用 expanded 接收。
    hits = retrieve(query, top_k)
    expanded = expand_context_chunks(chunks, hits, window)
    # TODO 2：调用 prioritize_hits(hits, expanded)，用 candidates 接收。
    # 然后调用 select_context(query, candidates, input_budget, count_messages)，
    # 用 selection 接收。这里已经得到最终 messages 和最终来源数。
    candidates = prioritize_hits(hits, expanded)
    selection = select_context(query, candidates, input_budget, count_messages)

    # TODO 3：返回 finish_run(hits, selection, generate)。
    # 不要另外调用 generate，也不要重建 messages，否则会重复生成或绕过预算。
    return finish_run(hits, selection, generate)


def main() -> None:
    chunks, hits = make_example()

    def fake_retrieve(query: str, k: int) -> list[dict]:
        print("检索输入：", query, "top_k=", k)
        return hits[:k]

    def fake_generate(messages: list[dict[str, str]]) -> str:
        print("实际交给假生成器的 user 消息：\n", messages[1]["content"])
        # 演示只命中 A_001，优先命中后为 A_001、A_000、A_002，原因在 [3]。
        return "根据学习资料，他选择那里是因为当地有图书馆，便于学习。[3]"

    result = run_rag(
        "练习角色为什么选择示例地区？", chunks, fake_retrieve, fake_generate,
        input_budget=2000, count_messages=demo_character_count, top_k=1, window=1,
    )
    print("最终报告（演示字符单位，不是 Token）：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
