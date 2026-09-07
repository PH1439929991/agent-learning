"""多工具 Function Calling 练习。

学习目标：
1. 实现 list_champions。
2. 为 list_champions 编写工具 schema。
3. 把第二个工具加入注册表，让模型在两个工具之间路由。

运行方式：
    .venv/bin/python src/agent_learning/module_04_tool_schema/agent.py
    或按模块运行：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_04_tool_schema.agent
"""

import json
import sys
from pathlib import Path
from typing import Any, Callable

# 直接运行本文件时，将 src 加入搜索路径，让 Python 能找到 agent_learning 包。
# 使用 python -m 启动或被其他模块导入时，无需修改搜索路径。
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic import ValidationError

from agent_learning.common.llm_client import LLMClient
from agent_learning.module_03_function_calling.champion_tools import (
    get_champion_info,
    list_champions,
)
from agent_learning.module_04_tool_schema.argument_models import (
    GetChampionInfoArguments,
    ListChampionsArguments,
)
from agent_learning.module_04_tool_schema.schema_builder import build_all_tool_schemas, build_tool_schema



SYSTEM_PROMPT = """
# 角色

你是一名《英雄联盟》背景资料助手，只根据工具返回的数据回答问题。

# 工具使用规则

- 查询某个具体英雄的背景、称号、地区、关键事件或关联人物时，调用 get_champion_info。
- 查询资料库有哪些英雄，或者查询某个地区有哪些英雄时，调用 list_champions。
- 普通寒暄不调用工具。
- 用户没有提供查询所需的信息时，先请用户补充，不要猜测参数。

# 回答规则

- 不得编造工具结果中不存在的英雄资料。
- 工具返回 success=false 时，明确说明没有查到结果。
- 使用简洁、自然的中文整理工具结果，不直接展示原始 JSON。
""".strip()


TOOLS = []


ToolFunction = Callable[..., dict]

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "get_champion_info":{
        "function": get_champion_info,
        "description": "根据中文名、英文名或称号查询某个英雄的背景资料。",
        "arguments_model": GetChampionInfoArguments,
    } ,
    "list_champions": {
        "function": list_champions,
        "description": "列出资料库中的英雄；传入 region 时，只返回该地区的英雄。",
        "arguments_model": ListChampionsArguments,
    }
}

for name, config in TOOL_REGISTRY.items():
    TOOLS.append(
        build_tool_schema(
            name,
            config["description"],
            config["arguments_model"],
        )
    )

def execute_tool_call(tool_call: Any) -> dict:
    """解析模型生成的参数，并执行注册表中的对应函数。"""
    function_name = tool_call.function.name

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        return {
            "success": False,
            "message": f"工具参数不是合法 JSON：{error}",
        }

    tool_config = TOOL_REGISTRY.get(function_name)
    if tool_config is None:
        return {
            "success": False,
            "message": f"未注册的工具：{function_name}",
        }

    try:
        arguments_model = tool_config["arguments_model"]
        validated_arguments = arguments_model.model_validate(arguments)
    except ValidationError as error:
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "工具参数校验失败",
            "details": [
                {
                    "field": ".".join(
                        str(item) for item in detail["loc"]
                    ),
                    "message": detail["msg"],
                    "type": detail["type"],
                }
                for detail in error.errors()
            ],
        }

    tool_function = tool_config["function"]

    try:
        return tool_function(**validated_arguments.model_dump())
    except TypeError as error:
        return {
            "success": False,
            "error_type": "tool_argument_error",
            "message": f"工具参数不匹配：{error}",
        }


def ask_agent(question: str, max_tool_rounds: int = 5) -> str:
    """向模型提问，并循环处理它返回的一个或多个工具调用。"""
    llm = LLMClient()
    messages: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]



    for _ in range(max_tool_rounds):
        response = llm.client.chat.completions.create(
            model=llm.model,
            temperature=llm.temperature,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        tool_calls = assistant_message.tool_calls or []
        if not tool_calls:
            return assistant_message.content or "模型没有返回文本内容"

        for tool_call in tool_calls:
            print(
                f"[工具调用] {tool_call.function.name}"
                f"({tool_call.function.arguments})"
            )

            tool_result = execute_tool_call(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    raise RuntimeError("工具调用轮次过多，已停止执行")


def main() -> None:
    print("多工具英雄资料助手（输入 exit 退出）")

    while True:
        try:
            question = input("你：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n对话已结束")
            break

        if question.lower() in {"exit", "quit", "退出"}:
            print("对话已结束")
            break

        if not question:
            print("输入不能为空")
            continue

        try:
            print(f"助手：{ask_agent(question)}")
        except NotImplementedError as error:
            print(f"练习尚未完成：{error}")


if __name__ == "__main__":
    main()
