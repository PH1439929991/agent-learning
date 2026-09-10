"""异常分类练习：决定一个失败是否应该重试。"""

import logging

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

from agent_learning.module_06_observability.logging_basics import configure_logging
from agent_learning.module_07_reliability.retry_basics import TemporaryToolError


logger = logging.getLogger(__name__)


# TODO 1：把可以重试的异常类型放进这个元组。
# 包括 APITimeoutError、APIConnectionError、RateLimitError、
# InternalServerError 和 TemporaryToolError。
RETRYABLE_ERRORS: tuple[type[Exception], ...] = ()


def should_retry(error: Exception) -> bool:
    """如果异常属于临时性故障，返回 True。"""
    # TODO 2：使用 isinstance(error, RETRYABLE_ERRORS) 完成判断。
    return False


def execute_with_error_policy(operation, max_attempts: int = 3):
    """只重试策略允许的异常；其他异常立即向上抛出。"""
    if max_attempts < 1:
        raise ValueError("max_attempts 必须大于等于 1")

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as error:
            # TODO 3：如果 should_retry(error) 为 False，
            # 记录“不可重试”日志，然后使用 raise 立即失败。

            logger.warning(
                "发生可重试错误 | attempt=%s/%s | error_type=%s | error=%s",
                attempt,
                max_attempts,
                type(error).__name__,
                error,
            )
            if attempt == max_attempts:
                raise

    raise RuntimeError("重试循环意外结束")


class SequenceOperation:
    """按顺序抛出异常或返回结果的测试操作。"""

    def __init__(self, outcomes: list) -> None:
        self.outcomes = outcomes
        self.calls = 0

    def __call__(self):
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def main() -> None:
    configure_logging()
    operation = SequenceOperation(
        [
            TemporaryToolError("工具暂时不可用"),
            {"success": True},
        ]
    )
    result = execute_with_error_policy(operation)
    print(f"执行结果：{result}，调用次数：{operation.calls}")


if __name__ == "__main__":
    main()
