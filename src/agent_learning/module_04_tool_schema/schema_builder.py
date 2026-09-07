"""使用 Pydantic 自动生成 Function Calling schema 的练习。

学习目标：
1. 使用 model_json_schema() 查看参数模型对应的 JSON Schema。
2. 理解 Pydantic 字段规则如何映射到 JSON Schema。
3. 实现 build_tool_schema()，组装模型接口需要的工具结构。
4. 使用一份工具配置生成多个 Function Calling 工具。

运行方式：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_04_tool_schema.schema_builder

说明：
    当前练习不会修改同目录的 agent.py。
    先观察程序打印的参数 schema，再完成 TODO 1。
"""

import json
from typing import Any

from pydantic import BaseModel

from agent_learning.module_04_tool_schema.argument_models import (
    GetChampionInfoArguments,
    ListChampionsArguments,
)


TOOL_SPECS = [
    {
        "name": "get_champion_info",
        "description": "根据中文名、英文名或称号查询某个英雄的背景资料。",
        "arguments_model": GetChampionInfoArguments,
    },
    {
        "name": "list_champions",
        "description": "列出资料库中的英雄；传入 region 时，只返回该地区的英雄。",
        "arguments_model": ListChampionsArguments,
    },
]


def print_json(title: str, value: Any) -> None:
    """以便于阅读的格式打印 Python 对象。"""
    print(f"\n=== {title} ===")
    print(json.dumps(value, ensure_ascii=False, indent=2))


def show_argument_model_schemas() -> None:
    """展示两个 Pydantic 参数模型自动生成的 JSON Schema。"""
    for tool_spec in TOOL_SPECS:
        arguments_model = tool_spec["arguments_model"]
        parameters_schema = arguments_model.model_json_schema()

        print_json(
            f"{arguments_model.__name__}.model_json_schema()",
            parameters_schema,
        )


def build_tool_schema(
    name: str,
    description: str,
    arguments_model: type[BaseModel],
) -> dict[str, Any]:
    """使用 Pydantic 参数模型生成一个 Function Calling 工具 schema。"""
    # TODO 1：返回一个完整的工具 schema。
    #
    # 最外层需要：
    #     "type": "function"
    #     "function": {...}
    #
    # function 中需要：
    #     "name": name
    #     "description": description
    #     "parameters": arguments_model 自动生成的 JSON Schema
    TOOL = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": arguments_model.model_json_schema(),
        }
    }
    return TOOL


def build_all_tool_schemas() -> list[dict[str, Any]]:
    """遍历统一配置，为所有工具生成 schema。"""
    tools = []

    for tool_spec in TOOL_SPECS:
        tools.append(
            build_tool_schema(
                name=tool_spec["name"],
                description=tool_spec["description"],
                arguments_model=tool_spec["arguments_model"],
            )
        )

    return tools


def check_tool_schema(
    tool_schema: dict[str, Any],
    tool_spec: dict[str, Any],
) -> list[str]:
    """检查生成结果是否符合本次练习要求。"""
    problems = []

    if tool_schema.get("type") != "function":
        problems.append("最外层 type 应该等于 function")

    function_schema = tool_schema.get("function")
    if not isinstance(function_schema, dict):
        problems.append("最外层缺少 function 字典")
        return problems

    if function_schema.get("name") != tool_spec["name"]:
        problems.append("function.name 不正确")

    if function_schema.get("description") != tool_spec["description"]:
        problems.append("function.description 不正确")

    expected_parameters = tool_spec["arguments_model"].model_json_schema()
    if function_schema.get("parameters") != expected_parameters:
        problems.append("function.parameters 不是参数模型生成的 schema")

    return problems


def check_parameter_rules(tools: list[dict[str, Any]]) -> list[str]:
    """检查两个参数模型中最关键的必填和默认值规则。"""
    problems = []
    tools_by_name = {
        tool["function"]["name"]: tool
        for tool in tools
    }

    champion_parameters = tools_by_name[
        "get_champion_info"
    ]["function"]["parameters"]
    champion_required = champion_parameters.get("required", [])

    if "champion_name" not in champion_required:
        problems.append("champion_name 应该是必填参数")

    champion_property = champion_parameters.get(
        "properties", {}
    ).get("champion_name", {})
    if champion_property.get("minLength") != 1:
        problems.append("champion_name 的 minLength 应该等于 1")

    list_parameters = tools_by_name[
        "list_champions"
    ]["function"]["parameters"]
    list_required = list_parameters.get("required", [])

    if "region" in list_required:
        problems.append("region 应该是可选参数")

    region_property = list_parameters.get(
        "properties", {}
    ).get("region", {})
    if region_property.get("default") != "":
        problems.append("region 的默认值应该是空字符串")

    for name, tool in tools_by_name.items():
        parameters = tool["function"]["parameters"]
        if parameters.get("additionalProperties") is not False:
            problems.append(f"{name} 应该禁止额外参数")

    return problems


def main() -> None:
    show_argument_model_schemas()

    print("\n=== 生成完整工具 schema ===")

    try:
        tools = build_all_tool_schemas()
    except NotImplementedError as error:
        print(f"练习尚未完成：{error}")
        return

    all_problems = []

    for tool_schema, tool_spec in zip(tools, TOOL_SPECS):
        print_json(
            f"生成结果：{tool_spec['name']}",
            tool_schema,
        )
        all_problems.extend(
            check_tool_schema(tool_schema, tool_spec)
        )

    all_problems.extend(check_parameter_rules(tools))

    print("\n=== 检查结果 ===")
    if all_problems:
        for problem in all_problems:
            print(f"[未通过] {problem}")
        print(f"共发现 {len(all_problems)} 个问题，请继续修改 TODO 1。")
    else:
        print("[通过] 两个工具 schema 均由 Pydantic 正确生成。")
        print("下一步可以使用这份配置替换同目录 agent.py 中的手写 TOOLS。")


if __name__ == "__main__":
    main()
