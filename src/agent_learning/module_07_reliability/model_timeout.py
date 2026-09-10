"""模型请求超时练习：限制单次 HTTP 请求的最长等待时间。"""

import logging
from time import perf_counter

from openai import APITimeoutError

from agent_learning.common.llm_client import LLMClient
from agent_learning.module_06_observability.logging_basics import configure_logging


logger = logging.getLogger(__name__)


def generate_with_timeout(
    llm: LLMClient,
    messages: list[dict[str, str]],
    timeout_seconds: float = 10.0,
) -> str:
    """调用模型；超过 timeout_seconds 时抛出 APITimeoutError。"""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds 必须大于 0")

    # TODO 1：创建本次请求使用的客户端副本。
    # 使用 llm.client.with_options(...)，传入：
    # timeout=timeout_seconds, max_retries=0
    request_client = llm.client.with_options(
        timeout=timeout_seconds, max_retries=0
    )

    started_at = perf_counter()
    logger.info(
        "模型调用开始 | model=%s | timeout_seconds=%.2f",
        llm.model,
        timeout_seconds,
    )

    try:
        # TODO 2：使用 request_client 发起 chat.completions.create 请求。
        # 参数为 model、temperature 和 messages。
        response = request_client.chat.completions.create(
            model=llm.model, temperature=llm.temperature, messages=messages
        )
    except APITimeoutError as error:
        duration_ms = (perf_counter() - started_at) * 1000

        # TODO 3：记录 WARNING 日志，包含 model、timeout_seconds、
        # duration_ms 和 error，然后使用 raise 重新抛出原异常。
        logger.warning(
            "模型调用超时 | model=%s | timeout_seconds=%.2f | "
            "duration_ms=%.2f | error=%s",
            llm.model,
            timeout_seconds,
            duration_ms,
            error,
        )
        raise

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("模型没有返回文本内容")
    return content


def main() -> None:
    configure_logging()
    llm = LLMClient()
    messages = [
        {"role": "user", "content": "请用一句话介绍亚索。"},
    ]
    answer = generate_with_timeout(llm, messages, timeout_seconds=10.0)
    print(f"最终回答：{answer}")


if __name__ == "__main__":
    main()
