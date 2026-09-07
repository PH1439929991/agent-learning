"""英雄背景查询 Agent：Function Calling 练习框架。

运行方式：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_03_function_calling.single_tool_agent

本练习需要完成标记为 TODO 的三处核心代码。
"""

import json
from typing import Any

from agent_learning.common.llm_client import LLMClient
from agent_learning.module_03_function_calling.champion_tools import get_champion_info


# TODO 1：编写 System prompt。
# 建议至少描述下面四件事：
# 1. 模型扮演什么角色。
# 2. 什么情况下必须调用 get_champion_info。
# 3. 工具没有找到英雄时应该怎么回答。
# 4. 普通寒暄是否需要调用工具。
SYSTEM_PROMPT = """
1.你是谁？
你是一位《英雄联盟》的专业助手，专门回答用户关于游戏中英雄的背景资料问题。

2.你要完成什么任务？
回答用户关于游戏中英雄的背景资料问题。

3.什么时候调用工具？
    - 当用户询问英雄的背景、称号、所属地区、关键事件或关联人物时、英文名或称号时，必须调用 get_champion_info。
    - 当用户问题中不包含英雄的中文名、英文名或称号时，不能调用 get_champion_info。

4.事实必须来自哪里？
    - 你必须使用 get_champion_info 工具来获取英雄的背景资料。

5.工具没有找到英雄时应该怎么回答？
    - 如果工具没有找到英雄,明确告诉用户当前资料库中没有该英雄。
    - 普通寒暄不调工具,直接正常回答

6.普通寒暄是否需要调用工具？
    - 不需要调用工具。
"""


# 这是提供给模型看的“工具说明书”，不是实际执行的 Python 函数。
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_champion_info",
            "description": "根据中文名、英文名或称号查询英雄联盟英雄的背景资料。",
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
    }
]


# TODO 2：完成工具注册表。
# 提示：键是模型返回的函数名字符串，值是上面导入的 Python 函数对象。
TOOL_REGISTRY: dict[str, Any] = {
    # 在这里填写你的代码
    "get_champion_info": get_champion_info
}


def execute_tool_call(tool_call: Any) -> dict:
    """根据模型返回的 tool call，找到并执行本地 Python 函数。"""
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    # TODO 3：完成下面三步。
    # 1. 使用 function_name 从 TOOL_REGISTRY 中查找函数。
    function = TOOL_REGISTRY.get(function_name)
    # 2. 如果函数不存在，返回一个包含 success=False 的字典。
    if not function:
        return {"success": False}
    # 3. 如果函数存在，使用 arguments 调用函数并返回执行结果。
    else:
        return function(**arguments)



def ask_champion(question: str, max_tool_rounds: int = 5) -> str:
    """向模型提问，并负责完成工具调用循环。"""
    llm = LLMClient()
    messages: list[Any] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": question,
        },
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
    print("英雄背景查询助手（输入 exit 退出）")

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
            answer = ask_champion(question)
            print(f"助手：{answer}")
        except NotImplementedError as error:
            print(f"练习尚未完成：{error}")


if __name__ == "__main__":
    main()
