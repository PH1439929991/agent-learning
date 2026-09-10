"""基础重试练习：只重试临时错误，并限制最大尝试次数。"""

import logging

from agent_learning.module_06_observability.logging_basics import configure_logging

logger = logging.getLogger(__name__)


class TemporaryToolError(RuntimeError):
    """可以重试的临时错误，例如超时或服务暂时不可用。"""


class FlakyTool:
    """前几次失败、到指定次数才成功的假工具。"""

    def __init__(self, succeed_on_attempt: int) -> None:
        self.succeed_on_attempt = succeed_on_attempt
        self.attempts = 0

    def __call__(self) -> dict:
        self.attempts += 1
        if self.attempts < self.succeed_on_attempt:
            raise TemporaryToolError("工具服务暂时不可用")

        return {"success": True, "attempts": self.attempts}


def execute_with_retry(operation, max_attempts: int = 3) -> dict:
    """执行操作；遇到 TemporaryToolError 时进行有限次数重试。"""
    # TODO 1：使用 range(1, max_attempts + 1) 遍历 attempt。
    if max_attempts <= 0:
        raise ValueError("max_attempts 必须大于 0")
    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except TemporaryToolError as error:
            logger.warning(
                "工具临时失败 | attempt=%s/%s | error=%s",
                attempt,
                max_attempts,
                error,
            )
            if attempt == max_attempts:
                raise


def main() -> None:
    configure_logging()
    tool = FlakyTool(succeed_on_attempt=3)
    result = execute_with_retry(tool, max_attempts=3)
    print(f"工具结果：{result}")


if __name__ == "__main__":
    main()
