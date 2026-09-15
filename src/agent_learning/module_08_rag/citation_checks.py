"""RAG 第九节：检查回答引用的编号是否存在。

只完成 check_citations() 的三个 TODO。本文件不调用模型，不修改回答。
编号有效不等于内容有依据；这里只检查形如 [1] 的半角数字引用。
"""

import re


def extract_citation_numbers(answer: str) -> list[int]:
    """已完成：提取 [1]、[2] 这种编号，去重后从小到大排列。

    re.findall 返回匹配到的数字字符串，例如 ['2', '1', '2']。
    int 转整数，集合去重，sorted 排序，最终得到 [1, 2]。
    本节约定编号无前导零；[01]、[1,2]、[来源1] 不属于支持的格式。
    [0] 会被提取，由下面的范围检查判定无效。
    """
    matches = re.findall(r"\[(0|[1-9][0-9]*)\]", answer)
    return sorted({int(number) for number in matches})


def check_citations(answer: str, source_count: int) -> dict:
    """练习：检查编号是否落在 1 到 source_count 之间（包含两端）。

    answer：模型生成的回答，例如“角色住在示例地区。[1]”。
    source_count：实际发送给模型的资料条数，例如 len(hits)，不是全库大小。

    返回示例：answer 含 [1] 和 [3]，source_count=2：
    {
        "cited_numbers": [1, 3],
        "invalid_numbers": [3],
        "has_citations": True,
        "references_valid": False,
    }

    references_valid 只有在“存在引用且所有编号都有效”时才为 True。
    没引用时为 False，但不等于回答错误：合理拒答也可以没有引用。
    """
    if not answer.strip():
        raise ValueError("answer 不能为空")
    if type(source_count) is not int or source_count < 0:
        raise ValueError("source_count 必须是非负整数")

    # TODO 1：调用 extract_citation_numbers(answer)，用 cited_numbers 接收。
    cited_numbers = extract_citation_numbers(answer)
    # TODO 2：创建 invalid_numbers = []，遍历 cited_numbers。
    # 如果 number < 1 或 number > source_count，把它追加到 invalid_numbers。
    invalid_numbers = [number for number in cited_numbers if number < 1 or number > source_count]
    # TODO 3：返回包含上述四个字段的字典。
    # has_citations 使用 bool(cited_numbers)。
    # references_valid 要同时满足“有引用”和“invalid_numbers 为空”。
    return{
        "cited_numbers": cited_numbers,
        "invalid_numbers": invalid_numbers,
        "has_citations": bool(cited_numbers),
        "references_valid": bool(cited_numbers) and not invalid_numbers,
    }



def main() -> None:
    # 手写回答只用于检验规则，不是真实模型输出。
    examples = [
        ("正常编号", "根据学习资料，角色住在示例地区。[1]", 2),
        ("编号越界", "根据学习资料，角色住在示例地区。[3]", 2),
        ("部分越界", "角色喜欢阅读。[1] 角色喜欢游泳。[3]", 2),
        ("没有引用", "角色住在示例地区。", 2),
        ("合理拒答也可无引用", "资料不足，无法回答。", 2),
        ("零不是有效编号", "角色住在示例地区。[0]", 2),
    ]
    for name, answer, source_count in examples:
        print(f"\n{name} | 实际提供 {source_count} 段资料")
        print("回答：", answer)
        print("检查：", check_citations(answer, source_count))
    print("\n注意：编号存在≠正文支持回答；此检查不判断事实、相关性或拒答是否合理。")


if __name__ == "__main__":
    main()
