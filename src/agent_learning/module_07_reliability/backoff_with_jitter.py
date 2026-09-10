"""带上限和随机抖动的指数退避练习。"""

import logging
from random import uniform
from time import sleep
from typing import Callable

from agent_learning.module_06_observability.logging_basics import configure_logging
from agent_learning.module_07_reliability.retry_basics import (
    FlakyTool,
    TemporaryToolError,
)


logger = logging.getLogger(__name__)


def execute_with_jitter(
    operation,
    max_attempts: int = 5,
    base_delay: float = 0.2,
    max_delay: float = 0.5,
    sleep_function: Callable[[float], None] = sleep,
    jitter_function: Callable[[float, float], float] = uniform,
) -> dict:
    """使用有上限的指数退避和随机抖动。"""
    if max_attempts < 1:
        raise ValueError("max_attempts 必须大于等于 1")
    if base_delay < 0 or max_delay < 0:
        raise ValueError("base_delay 和 max_delay 不能小于 0")

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

            # TODO 1：计算原始指数退避时间 raw_delay。
            raw_delay = base_delay * (2 ** (attempt - 1))
            # TODO 2：用 min() 限制最大等待时间。
            capped_delay = min(raw_delay, max_delay)
            # TODO 3：在 0 到 capped_delay 之间生成实际等待时间。
            delay_seconds = jitter_function(0, capped_delay)

            logger.warning(
                "工具临时失败，抖动后重试 | attempt=%s/%s | "
                "capped_delay=%.2f | delay_seconds=%.2f | error=%s",
                attempt,
                max_attempts,
                capped_delay,
                delay_seconds,
                error,
            )
            sleep_function(delay_seconds)

    raise RuntimeError("重试循环意外结束")


def main() -> None:
    configure_logging()
    tool = FlakyTool(succeed_on_attempt=5)
    result = execute_with_jitter(tool)
    print(f"工具结果：{result}")


if __name__ == "__main__":
    main()
