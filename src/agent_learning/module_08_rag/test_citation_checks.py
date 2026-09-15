"""引用编号校验练习；全部离线，exercise 用例需要学生完成 TODO。"""

import pytest

from agent_learning.module_08_rag.citation_checks import (
    check_citations, extract_citation_numbers,
)


@pytest.mark.parametrize(
    "answer,count,cited,invalid,valid",
    [
        ("有依据。[1]", 2, [1], [], True),
        ("有依据。[2][1][2]", 2, [1, 2], [], True),
        ("越界引用。[3]", 2, [3], [3], False),
        ("部分越界。[1][3]", 2, [1, 3], [3], False),
        ("编号不能为零。[0]", 2, [0], [0], False),
        ("有回答但无引用。", 2, [], [], False),
        ("资料不足，无法回答。", 0, [], [], False),
        ("没资料却引用。[1]", 0, [1], [1], False),
    ],
)
def test_exercise_citation_report(answer, count, cited, invalid, valid):
    assert check_citations(answer, count) == {
        "cited_numbers": cited,
        "invalid_numbers": invalid,
        "has_citations": bool(cited),
        "references_valid": valid,
    }


def test_extract_numbers():
    assert extract_citation_numbers("正文[12][2][12][0]") == [0, 2, 12]


def test_supported_format_only():
    assert extract_citation_numbers("[来源1]、[1,2]、[01]、［1］") == []


@pytest.mark.parametrize("count", [-1, True, 1.5])
def test_invalid_source_count(count):
    with pytest.raises(ValueError, match="source_count"):
        check_citations("回答[1]", count)


def test_empty_answer():
    with pytest.raises(ValueError, match="answer 不能为空"):
        check_citations("  ", 2)
