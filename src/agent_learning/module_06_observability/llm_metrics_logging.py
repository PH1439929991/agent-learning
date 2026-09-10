"""记录 LLM 调用的耗时和 Token 指标。"""

import logging
from time import perf_counter
from uuid import uuid4

from agent_learning.common.llm_client import LLMClient
from agent_learning.module_06_observability.logging_basics import configure_logging


logger = logging.getLogger(__name__)


def generate_with_metrics(
    llm: LLMClient,
    request_id: str,
    messages: list[dict[str, str]],
) -> str:
    """调用模型，并记录本次调用的指标。"""
    logger.info(
        "模型调用开始 | request_id=%s | model=%s | message_count=%s",
        request_id,
        llm.model,
        len(messages),
    )
    started_at = perf_counter()

    try:
        response = llm.client.chat.completions.create(
            model=llm.model,
            temperature=llm.temperature,
            messages=messages,
        )
    except Exception as error:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "模型调用失败 | request_id=%s | model=%s "
            "| duration_ms=%.2f | error=%s",
            request_id,
            llm.model,
            duration_ms,
            error,
        )
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    try:
        usage = response.usage
        if usage is None:
            raise ValueError("response.usage 为空")

        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
    except (AttributeError, ValueError) as error:
        logger.warning(
            "模型 Token 指标缺失 | request_id=%s | model=%s | error=%s",
            request_id,
            llm.model,
            error,
        )
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

    # TODO 3：记录完成日志，包含 request_id、model、duration_ms
    # 以及 prompt_tokens、completion_tokens、total_tokens。
    logger.info(
        "模型调用完成 | request_id=%s | model=%s | duration_ms=%.2f "
        "| prompt_tokens=%s | completion_tokens=%s | total_tokens=%s",
        request_id,
        llm.model,
        duration_ms,
        prompt_tokens,
        completion_tokens,
        total_tokens,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("模型没有返回文本内容")
    return content


def main() -> None:
    configure_logging()
    llm = LLMClient()
    request_id = uuid4().hex[:8]
    messages = [
        {"role": "system", "content": "你是简洁的英雄联盟资料助手。"},
        {"role": "user", "content": "请用一句话介绍亚索。"},
    ]
    answer = generate_with_metrics(llm, request_id, messages)
    print(f"最终回答：{answer}")


if __name__ == "__main__":
    main()
