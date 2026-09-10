"""五个已完成的工具执行器测试。

在项目根目录运行：
    PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_05_testing -v

pytest 自动寻找 test_ 开头的函数；无需手动调用它们。
本文件使用本地工具，不调用模型 API。

执行工具前有两道检查：JSON 解析 → Pydantic 参数校验。
- JSON 少了右花括号：解析失败，不执行工具，calls 为 []。
- champion_name=""：JSON 合法，但不满足 min_length=1，不执行工具。
- champion_name="亚索"：两道检查通过，才能执行工具。
- region=""：地区参数允许空字符串，表示查询全部英雄，可以执行工具。
calls 不会自动记录；只有替身工具执行 calls.append(arguments) 才会增加记录。
"""

import json
from types import SimpleNamespace

from agent_learning.module_04_tool_schema.agent import (
    TOOL_REGISTRY,
    execute_tool_call,
)


def make_call(name: str, arguments: dict) -> SimpleNamespace:
    """模拟 SDK 工具调用对象，arguments 转为接口使用的 JSON 字符串。"""
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments, ensure_ascii=False),
        )
    )


def test_query_champion_success():
    """示例一：准备输入 → 执行 → 断言结果。"""
    tool_call = make_call("get_champion_info", {"champion_name": "亚索"})

    result = execute_tool_call(tool_call)

    # assert 表示：期望这个条件成立；不成立则测试失败。
    assert result["success"] is True
    # 不能只检查 success，还要确认查到的是目标英雄。
    assert result["champion_data"]["name_cn"] == "亚索"


def test_invalid_argument_never_executes_tool(monkeypatch):
    """示例二：空英雄名必须被校验拦截，真实工具不能执行。"""
    calls = []

    def recording_tool(**arguments):
        calls.append(arguments)
        return {"success": True}

    # 临时替换这个工具的实现；测试结束后 pytest 会恢复原来的函数。
    monkeypatch.setitem(
        TOOL_REGISTRY["get_champion_info"], "function", recording_tool
    )

    result = execute_tool_call(
        make_call("get_champion_info", {"champion_name": ""})
    )

    assert result["success"] is False
    assert result["error_type"] == "validation_error"
    assert any(
        detail["field"] == "champion_name"
        and detail["type"] == "string_too_short"
        for detail in result["details"]
    )
    assert calls == [], "校验失败时，不应该调用工具函数"
    # 错误结果需要能放回 tool 消息；无法转成 JSON 时本行会报错。
    json.dumps(result, ensure_ascii=False)


def test_default_region_is_empty_string(monkeypatch):
    """练习一：不传 region 时，工具实际收到的应是空字符串。"""
    # 1. 在执行器调用前，准备一个记录参数的替身工具。
    calls = []

    def recording_tool(**arguments):
        # **arguments 将收到的关键字参数收集为字典。
        calls.append(arguments)
        return {"success": True}

    # 2. pytest 提供 monkeypatch；临时替换工具，测试结束后自动恢复。
    # 执行器仍然使用真实的参数校验逻辑，但最终调用这个替身。
    monkeypatch.setitem(
        TOOL_REGISTRY["list_champions"], "function", recording_tool
    )

    # 3. 故意不传 region，检查执行器是否通过校验类补上默认值。
    tool_call = make_call("list_champions", {})
    result = execute_tool_call(tool_call)

    # 4. result 是替身的返回值，calls 才是它实际收到的参数记录。
    assert result["success"] is True
    assert calls == [{"region": ""}]



def test_unknown_tool_returns_failure():
    """练习二：调用未注册的工具应该得到失败结果。"""
    # 1. 使用 make_call("unknown_tool", {}) 构造调用。
    # 2. 调用 execute_tool_call。
    # 3. 断言 success 为 False，且 message 包含 unknown_tool。
    tool_call = make_call("unknown_tool", {})

    result = execute_tool_call(tool_call)

    assert result["success"] is False
    assert "unknown_tool" in result["message"]


def test_invalid_json_returns_failure(monkeypatch):
    """练习三：非法 JSON 应在解析阶段被拦截。"""
    calls = []

    def recording_tool(**arguments):
        # 访问外层的同一个列表；每执行一次，就追加一条参数记录。
        # 这里只是定义函数，还没有执行，calls 仍然为空。
        calls.append(arguments)
        return {"success": True}

    # 临时把注册表中的真实工具换成记录员，测试结束后自动恢复。
    # 替换的是字典里的 function，不是工具调用对象的 arguments 属性。
    monkeypatch.setitem(
        TOOL_REGISTRY["get_champion_info"], "function", recording_tool
    )

    tool_call = make_call(
        "get_champion_info",
        {"champion_name": "亚索"},
    )

    # make_call 会生成合法 JSON，所以在这里故意改成缺少右花括号的字符串。
    tool_call.function.arguments = '{"champion_name": "亚索"'

    result = execute_tool_call(tool_call)

    assert result["success"] is False
    assert "工具参数不是合法 JSON" in result["message"]
    # JSON 解析已经失败，尚未进入 Pydantic 校验，更不会调用替身工具。
    # 没有执行 append，列表就保持为空。
    assert calls == [], "JSON 解析失败时，不应该调用工具函数"
