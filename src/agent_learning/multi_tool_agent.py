"""多工具 Function Calling 练习。

学习目标：
1. 实现 list_champions。
2. 为 list_champions 编写工具 schema。
3. 把第二个工具加入注册表，让模型在两个工具之间路由。

运行方式：
    .venv/bin/python src/agent_learning/multi_tool_agent.py
"""

import json
from pathlib import Path
from typing import Any, Callable

from LLM_client import LLMClient
from champions_tools import get_champion_info
from champions_tools import list_champions
from pydantic_tool_validation_exercise import (
    GetChampionInfoArguments,
    ListChampionsArguments,
)

DATA_FILE_PATH = Path(__file__).parent / "data" / "champions.json"


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


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_champion_info",
            "description": "根据中文名、英文名或称号查询某个英雄的背景资料。",
            "parameters": {
                "type": "object",
                "properties": {
                    "champion_name": {
                        "type": "string",
                        "description": "英雄中文名、英文名或称号，例如亚索、Yasuo、疾风剑豪。",
                    }
                },
                "required": ["champion_name"],
                "additionalProperties": False,
            },
        },
    },
    # TODO 2：在这里添加 list_champions 的工具 schema。
    #
    # 它可以接收一个可选的 region 字符串参数。
    # 注意：region 是可选参数，所以不要把它放进 required。
    {
        "type": "function",
        "function": {
            "name": "list_champions",
            "description": "列出资料库中的英雄；传入 region 时，只返回该地区的英雄。",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "英雄所属地区，例如艾欧尼亚、诺克萨斯、德玛西亚等。",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]


ToolFunction = Callable[..., dict]

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "get_champion_info":{
        "function": get_champion_info,
        "arguments_model": GetChampionInfoArguments,
    } ,
    # TODO 3：把 list_champions 注册到这里。
    "list_champions": {
        "function": list_champions,
        "arguments_model": ListChampionsArguments,
    }
}


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

    function = TOOL_REGISTRY.get(function_name)
    if function is None:
        return {
            "success": False,
            "message": f"未注册的工具：{function_name}",
        }

    try:
        Tool = function["function"]
        arguments_model = function["arguments_model"]
        validated_arguments = arguments_model.model_validate(arguments)
        return Tool(**validated_arguments.model_dump())

    except TypeError as error:
        return {
            "success": False,
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
