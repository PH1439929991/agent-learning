"""指数退避练习：每次重试前逐渐增加等待时间。"""

import logging
from collections.abc import Callable
from time import sleep

from agent_learning.module_06_observability.logging_basics import configure_logging
from agent_learning.module_07_reliability.retry_basics import (
    FlakyTool,
    TemporaryToolError,
)

logger = logging.getLogger(__name__)


def execute_with_backoff(
    operation,
    max_attempts: int = 4,
    base_delay: float = 0.2,
    sleep_function: Callable[[float], None] = sleep,
) -> dict:
    """重试临时错误，并在下一次尝试前执行指数退避。"""
    if max_attempts < 1:
        raise ValueError("max_attempts 必须大于等于 1")
    if base_delay < 0:
        raise ValueError("base_delay 不能小于 0")

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except TemporaryToolError as error:
            if attempt == max_attempts:
                logger.error(
                    "重试次数已耗尽 | attempt=%s/%s | error=%s",
                    attempt,
                    max_attempts,
                    error,
                )
                raise

            # TODO 1：计算等待时间。
            # 公式：base_delay * (2 ** (attempt - 1))
            delay_seconds = base_delay * (2 ** (attempt - 1))

            logger.warning(
                "工具临时失败，等待后重试 | attempt=%s/%s | "
                "delay_seconds=%.2f | error=%s",
                attempt,
                max_attempts,
                delay_seconds,
                error,
            )

            # TODO 2：调用 sleep_function，并传入 delay_seconds。
            sleep_function(delay_seconds)

    raise RuntimeError("重试循环意外结束")


def main() -> None:
    configure_logging()
    tool = FlakyTool(succeed_on_attempt=4)
    result = execute_with_backoff(tool)
    print(f"工具结果：{result}")


if __name__ == "__main__":
    main()
