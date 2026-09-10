"""工具耗时练习：记录工具开始、结果状态和执行时间。"""

import logging
from time import perf_counter

from agent_learning.module_03_function_calling.champion_tools import (
    get_champion_info,
)
from agent_learning.module_06_observability.logging_basics import (
    configure_logging,
)


logger = logging.getLogger(__name__)


def execute_tool_with_timing(
    tool_name: str,
    tool_function,
    arguments: dict,
) -> dict:
    """执行工具，并记录工具名称、结果状态和耗时。"""
    # perf_counter() 返回适合计算时间差的高精度计时值。
    start_time = perf_counter()

    logger.info(
        "工具执行开始 | tool_name=%s | arguments=%s",
        tool_name,
        arguments,
    )

    result = tool_function(**arguments)

    # TODO 1：工具结束后，再调用一次 perf_counter()，保存为 end_time。
    # TODO 2：计算毫秒耗时。
    # duration_ms = (end_time - start_time) * 1000
    end_time = perf_counter()
    logger.info(
        "工具执行完成 | tool_name=%s | success=%s | duration_ms=%.2f",
        tool_name,
        result.get("success"),
        (end_time - start_time) * 1000,
    )

    return result


def main() -> None:
    configure_logging()

    result = execute_tool_with_timing(
        tool_name="get_champion_info",
        tool_function=get_champion_info,
        arguments={"champion_name": "亚索"},
    )

    logger.info(
        "工具结果已交还调用方 | champion_name=%s",
        result["champion_data"]["name_cn"],
    )


if __name__ == "__main__":
    main()
