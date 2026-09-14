"""可靠模型调用综合练习：超时、分类、重试和退避。"""

import logging
from random import uniform
from time import sleep
from typing import Callable

from agent_learning.common.llm_client import LLMClient
from agent_learning.module_06_observability.logging_basics import configure_logging
from agent_learning.module_07_reliability.error_policy import should_retry


logger = logging.getLogger(__name__)


def generate_resiliently(
    llm: LLMClient,
    messages: list[dict[str, str]],
    max_attempts: int = 3,
    timeout_seconds: float = 10.0,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    sleep_function: Callable[[float], None] = sleep,
    jitter_function: Callable[[float, float], float] = uniform,
) -> str:
    """可靠地调用模型，并返回文本回答。"""
    if max_attempts < 1:
        raise ValueError("max_attempts 必须大于等于 1")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds 必须大于 0")
    if base_delay < 0 or max_delay < 0:
        raise ValueError("退避时间不能小于 0")

    # TODO 1：使用 with_options 创建请求客户端。
    # 设置 timeout=timeout_seconds，并设置 max_retries=0。
    request_client = llm.client.with_options(timeout=timeout_seconds, max_retries=0)

    for attempt in range(1, max_attempts + 1):
        try:
            # TODO 2：使用 request_client 发起模型请求。
            response = request_client.chat.completions.create(
                model=llm.model,
                messages=messages,
                temperature=llm.temperature,
            )

            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("模型没有返回文本内容")

            logger.info(
                "模型调用成功 | attempt=%s/%s | model=%s",
                attempt,
                max_attempts,
                llm.model,
            )
            return content
        except Exception as error:
            # TODO 3：如果错误不可重试，记录 ERROR 并立即 raise。
            if not should_retry(error):
                logger.error(
                    "发生不可重试错误 | attempt=%s/%s "
                    "| error_type=%s | error=%s",
                    attempt,
                    max_attempts,
                    type(error).__name__,
                    error,
                )
                raise
            if attempt == max_attempts:
                logger.error(
                    "模型重试次数耗尽 | attempt=%s/%s | error=%s",
                    attempt,
                    max_attempts,
                    error,
                )
                raise

            # TODO 4：计算 raw_delay、capped_delay 和 delay_seconds。
            raw_delay = base_delay * (2 ** (attempt - 1))
            capped_delay = min(raw_delay, max_delay)
            delay_seconds = jitter_function(0, capped_delay)

            logger.warning(
                "模型临时失败，等待后重试 | attempt=%s/%s | "
                "delay_seconds=%.2f | error_type=%s | error=%s",
                attempt,
                max_attempts,
                delay_seconds,
                type(error).__name__,
                error,
            )
            sleep_function(delay_seconds)

    raise RuntimeError("重试循环意外结束")


def main() -> None:
    configure_logging()
    llm = LLMClient()
    messages = [
        {"role": "user", "content": "请用一句话介绍亚索。"},
    ]
    answer = generate_resiliently(llm, messages)
    print(f"最终回答：{answer}")


if __name__ == "__main__":
    main()
