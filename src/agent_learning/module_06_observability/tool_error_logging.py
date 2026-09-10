"""工具异常日志练习：失败时记录耗时、错误信息和 traceback。"""

import logging
from time import perf_counter

from agent_learning.module_06_observability.logging_basics import configure_logging


logger = logging.getLogger(__name__)


def execute_tool_with_error_logging(
    tool_name: str,
    tool_function,
    arguments: dict,
) -> dict:
    """执行工具；成功和异常两条路径都会留下日志。"""
    start_time = perf_counter()
    logger.info(
        "工具执行开始 | tool_name=%s | arguments=%s",
        tool_name,
        arguments,
    )

    try:
        result = tool_function(**arguments)
    except Exception as error:
        duration_ms = (perf_counter() - start_time) * 1000

        logger.exception(
            "工具执行异常 | tool_name=%s | duration_ms=%.2f | error=%s",
            tool_name,
            duration_ms,
            error,
        )
        raise

    duration_ms = (perf_counter() - start_time) * 1000
    logger.info(
        "工具执行完成 | tool_name=%s | success=%s | duration_ms=%.2f",
        tool_name,
        result.get("success"),
        duration_ms,
    )
    return result


def broken_tool(champion_name: str) -> dict:
    """故意失败的假工具，用来练习异常日志。"""
    raise RuntimeError(f"模拟数据文件读取失败：{champion_name}")


def main() -> None:
    configure_logging()

    try:
        execute_tool_with_error_logging(
            tool_name="broken_tool",
            tool_function=broken_tool,
            arguments={"champion_name": "亚索"},
        )
    except RuntimeError as error:
        logger.warning("调用方捕获工具异常 | error=%s", error)


if __name__ == "__main__":
    main()
