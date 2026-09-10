"""request_id 日志练习：串联一次 Agent 请求中的所有关键步骤。"""

import logging
from uuid import uuid4

from agent_learning.module_03_function_calling.champion_tools import (
    get_champion_info,
)
from agent_learning.module_06_observability.logging_basics import configure_logging


logger = logging.getLogger(__name__)


def execute_tool(
    request_id: str,
    tool_name: str,
    tool_function,
    arguments: dict,
) -> dict:
    """执行工具，并把所属请求的 request_id 写入日志。"""
    # TODO 2：记录工具开始日志，包含 request_id、tool_name 和 arguments。
    logger.info(
        "工具执行开始 | request_id=%s | tool_name=%s | arguments=%s",
        request_id,
        tool_name,
        arguments,
    )

    result = tool_function(**arguments)

    logger.info(
        "工具执行完成 | request_id=%s | tool_name=%s | success=%s",
        request_id,
        tool_name,
        result.get("success"),
    )
    return result


def ask_agent(question: str) -> str:
    """模拟一次会调用英雄查询工具的 Agent 请求。"""
    # TODO 1：生成 request_id，取 uuid4().hex 的前 8 个字符。
    request_id = uuid4().hex[:8]

    logger.info(
        "Agent 请求开始 | request_id=%s | question=%s",
        request_id,
        question,
    )

    logger.info(
        "模型决定调用工具 | request_id=%s | tool_name=%s",
        request_id,
        "get_champion_info",
    )
    result = execute_tool(
        request_id=request_id,
        tool_name="get_champion_info",
        tool_function=get_champion_info,
        arguments={"champion_name": "亚索"},
    )

    champion_data = result["champion_data"]
    answer = f'{champion_data["name_cn"]}来自{champion_data["region"]}。'

    # TODO 3：记录 Agent 完成日志，包含 request_id 和 answer。
    logger.info(
        "Agent 请求完成 | request_id=%s | answer=%s",
        request_id,
        answer,
    )
    return answer


def main() -> None:
    configure_logging()
    answer = ask_agent("亚索来自哪里？")
    print(f"最终回答：{answer}")


if __name__ == "__main__":
    main()
