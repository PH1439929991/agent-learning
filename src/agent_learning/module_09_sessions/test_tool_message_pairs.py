"""第三节 A 离线验收：不调用模型，不执行实际工具。"""

from copy import deepcopy

import pytest

from agent_learning.module_09_sessions.tool_message_pairs import validate_tool_pairs


def assistant_calls(*ids):
    return {
        "role": "assistant", "content": None,
        "tool_calls": [
            {"id": call_id, "type": "function", "function": {
                "name": "search_knowledge", "arguments": '{"query":"练习角色"}',
            }} for call_id in ids
        ],
    }


def tool_result(call_id, content='{"success": true}'):
    return {"role": "tool", "tool_call_id": call_id, "content": content}


@pytest.mark.parametrize("messages", [
    [],
    [{"role": "system", "content": "规则"}, {"role": "user", "content": "你好"},
     {"role": "assistant", "content": "你好"}],
    [assistant_calls("A"), tool_result("A"), {"role": "assistant", "content": "答案"}],
    # 多工具结果按 ID 匹配，不要求 A、B 与发起时排列顺序相同。
    [assistant_calls("A", "B"), tool_result("B"), tool_result("A")],
    [assistant_calls("A"), tool_result("A"), assistant_calls("B"), tool_result("B")],
    # 工具业务失败也可以有完整的协议响应。
    [assistant_calls("A"), tool_result("A", '{"success": false, "message": "未找到"}')],
], ids=["empty", "plain-chat", "single", "reversed-results", "two-batches", "business-failure"])
def test_valid_pairs_return_none_without_mutation(messages):
    before = deepcopy(messages)
    assert validate_tool_pairs(messages) is None
    assert messages == before


@pytest.mark.parametrize("messages, error", [
    ([tool_result("A")], "没有对应"),
    ([assistant_calls("A"), tool_result("B")], "没有对应"),
    ([assistant_calls("A"), tool_result("A"), tool_result("A")], "没有对应"),
    ([assistant_calls("A")], "缺少工具结果"),
    ([assistant_calls("A", "B"), tool_result("A")], "缺少工具结果"),
    ([assistant_calls("A", "A")], "ID 重复"),
    ([assistant_calls("A"), {"role": "assistant", "content": "提前回答"}], "结果未齐"),
    ([assistant_calls("A"), {"role": "user", "content": "插话"}, tool_result("A")], "结果未齐"),
    ([tool_result("A"), assistant_calls("A")], "没有对应"),
    ([assistant_calls("A"), assistant_calls("B"), tool_result("A"), tool_result("B")], "结果未齐"),
], ids=["orphan", "wrong-id", "duplicate-result", "missing", "partly-missing",
        "duplicate-call", "early-answer", "interrupted", "result-before-call", "early-next-batch"])
def test_invalid_pairs_raise_without_mutation(messages, error):
    before = deepcopy(messages)
    with pytest.raises(ValueError, match=error):
        validate_tool_pairs(messages)
    assert messages == before


@pytest.mark.parametrize("messages", [
    None, ["not-a-message"],
    [assistant_calls("")], [tool_result(None)],
    [{"role": "assistant", "tool_calls": "not-a-list"}],
])
def test_provided_shape_guards(messages):
    with pytest.raises(ValueError):
        validate_tool_pairs(messages)
