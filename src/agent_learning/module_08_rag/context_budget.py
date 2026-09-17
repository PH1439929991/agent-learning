"""第十六节：按整组消息预算选择完整资料片段。纯离线。

只完成 select_context 的三个 TODO。
count_messages 可替换；演示用字符计数，不是模型 Token，也不能用于保证 API 不超限。
"""

from typing import Callable

from agent_learning.module_08_rag.rag_answering import build_rag_messages


def messages_for_chunks(query: str, chunks: list[dict]) -> list[dict[str, str]]:
    """已完成：按最终片段列表组装两条消息并重新编号，不传向量。"""
    return build_rag_messages(query, [{"chunk": chunk} for chunk in chunks])


def demo_character_count(messages: list[dict[str, str]]) -> int:
    """只计 role 与 content 字符数，用于稳定演示，不是 Token 估算器。"""
    return sum(len(message["role"]) + len(message["content"]) for message in messages)


def checked_size(messages: list[dict], count_messages: Callable) -> int:
    """已完成：计数回调须返回非负整数，同一输入须得到稳定结果。"""
    size = count_messages(messages)
    if type(size) is not int or size < 0:
        raise ValueError("计数函数必须返回非负整数")
    return size


def select_context(
    query: str,
    chunks: list[dict],
    input_budget: int,
    count_messages: Callable[[list[dict[str, str]]], int],
) -> dict:
    """练习：按输入顺序贪心选片段，超预算就跳过，继续尝试后面的片段。

    chunks 应是已经去重的候选片段；本函数不重新排序，不截断正文。
    input_budget 与 count_messages 必须采用同一种单位。
    保留 system 和当前问题：无资料的基础消息已超预算就报错，不删除它们。
    不保证找到最优组合；若候选来自邻居扩展，前面的邻居可能占用命中段预算。
    """
    if type(input_budget) is not int or input_budget < 0:
        raise ValueError("input_budget 必须是非负整数")
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    if len(set(chunk_ids)) != len(chunk_ids):
        raise ValueError("候选片段必须先按 ID 去重")
    base_messages = messages_for_chunks(query, [])
    if checked_size(base_messages, count_messages) > input_budget:
        raise ValueError("system 和问题组成的基础消息已超过输入预算")

    selected = []
    omitted = []
    # TODO 1：遍历 chunks，每次创建 candidate = [*selected, chunk]。
    # 调用 messages_for_chunks(query, candidate)，得到 candidate_messages。
    for chunk in chunks:
        candidate = [*selected, chunk]
        candidate_messages = messages_for_chunks(query, candidate)
        candidate_size = checked_size(candidate_messages, count_messages)

        if candidate_size <= input_budget:
            selected.append(chunk)
        else:
            omitted.append(chunk)
    # TODO 2：调用 checked_size(candidate_messages, count_messages) 计算整组消息大小。
    # <= input_budget：将完整 chunk 追加到 selected。
    # 否则：追加到 omitted，继续下一段（不能 break，也不修改原文）。
    selected_messages = messages_for_chunks(query, selected)
    input_size = checked_size(selected_messages, count_messages)
    # TODO 3：循环结束后，用 selected 重新构造 messages，返回字典：
    # messages、selected_chunks（selected）、omitted_chunks（omitted）、
    # input_size（最终 messages 的 checked_size）、input_budget、source_count（len(selected)）。
    return{
        "messages": selected_messages,
        "selected_chunks": selected,
        "omitted_chunks": omitted,
        "input_size": input_size,
        "input_budget": input_budget,
        "source_count": len(selected),
    }


def make_example() -> tuple[str, list[dict]]:
    query = "练习角色住在哪里，喜欢什么？"
    chunks = [{
        "chunk_id": chunk_id, "document_id": "demo", "text": text,
        "metadata": {"champion_name": "练习角色", "source_file": "离线演示"},
    } for chunk_id, text in [
        ("A", "练习角色住在示例地区。"),
        ("B", "这是一段很长的背景补充。" * 100),
        ("C", "练习角色喜欢阅读。"),
    ]]
    return query, chunks


def main() -> None:
    query, chunks = make_example()
    # 为了稳定演示，刻意设置成恰好装下 A、C 的预算。真实项目由模型限制决定预算。
    budget = demo_character_count(messages_for_chunks(query, [chunks[0], chunks[2]]))
    print("输入候选 ID：", [chunk["chunk_id"] for chunk in chunks])
    print("预算：", budget, "演示字符单位（不是 Token）")
    print("基础消息大小：", demo_character_count(messages_for_chunks(query, [])))
    for label, trial in [("尝试 A", chunks[:1]), ("尝试 A+B", chunks[:2]),
                         ("跳过 B 后尝试 A+C", [chunks[0], chunks[2]])]:
        print(label, "整组消息大小：", demo_character_count(messages_for_chunks(query, trial)))
    result = select_context(query, chunks, budget, demo_character_count)
    print("最终保留：", [chunk["chunk_id"] for chunk in result["selected_chunks"]])
    print("跳过：", [chunk["chunk_id"] for chunk in result["omitted_chunks"]])
    print("最终大小：", result["input_size"], "来源条数：", result["source_count"])
    print("最终 user 消息：\n", result["messages"][1]["content"])
    print("没有调用模型；字符预算不代表真实 Token 预算。")


if __name__ == "__main__":
    main()
