"""RAG 第十节：生成回答后，返回引用编号检查报告。

只完成 answer_with_citation_check() 的三个 TODO。
本文件的演示使用假生成函数，不调用真实模型；不会自动修正答案或重试。
"""

from typing import Callable

from agent_learning.module_08_rag.citation_checks import check_citations
from agent_learning.module_08_rag.rag_answering import answer_from_hits, demo_hits


def answer_with_citation_check(
    query: str,
    hits: list[dict],
    generate: Callable[[list[dict[str, str]]], str],
) -> dict:
    """练习：把上一节的检查器接在生成函数后面。

    query：用户问题。
    hits：最终要交给模型的片段列表；本函数不再过滤、扩展或去重。
    generate：接收 messages 并返回回答字符串的函数，不是回答字符串本身。

    返回结构：
    {
        "answer": "根据学习资料，练习角色居住在示例地区。[1]",
        "citation_check": {
            "cited_numbers": [1],
            "invalid_numbers": [],
            "has_citations": True,
            "references_valid": True,
        },
    }

    没有命中时，answer_from_hits 会本地返回“资料不足”，不调用 generate。
    即使引用检查失败，也保留原回答供排查，不删除引用、不自动重试。
    """
    # TODO 1：调用 answer_from_hits(query, hits, generate)，用 answer 接收。
    # 不要再自己组装 messages，也不要直接调用 generate(query)。

    # TODO 2：调用 check_citations(answer, source_count=len(hits))，
    # 用 citation_check 接收。这里数的是实际交给模型的片段，不是全库大小。

    # TODO 3：返回包含 answer 和 citation_check 两个字段的字典。
    raise NotImplementedError("请完成 answer_with_citation_check() 的三个 TODO")


def main() -> None:
    def fake_generate(messages: list[dict[str, str]]) -> str:
        print("假生成函数收到消息条数：", len(messages))
        # 故意返回越界引用：只给一段资料，却引用 [2]。
        return "根据学习资料，练习角色居住在示例地区。[2]"

    result = answer_with_citation_check(
        "练习角色居住在哪里？", demo_hits(), fake_generate
    )
    print("原始回答：", result["answer"])
    print("引用检查：", result["citation_check"])
    print("检查失败也保留原回答；这个报告不能证明回答的事实准确性。")


if __name__ == "__main__":
    main()
