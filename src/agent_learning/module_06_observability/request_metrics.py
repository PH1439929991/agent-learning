"""累计一次完整 Agent 请求中的模型与工具指标。"""

import logging
from dataclasses import dataclass
from uuid import uuid4

from agent_learning.module_06_observability.logging_basics import configure_logging


logger = logging.getLogger(__name__)


@dataclass
class AgentRunMetrics:
    """保存一次 Agent 请求的累计指标。"""

    request_id: str
    model_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def record_model_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> None:
        """把一轮模型请求的指标累加到本次 Agent 请求。"""
        # TODO 1：模型调用次数加 1，并累加三种 Token。
        self.model_calls += 1
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += total_tokens

    def record_tool_call(self) -> None:
        """记录一次工具调用。"""
        # TODO 2：工具调用次数加 1。
        self.tool_calls += 1
    def log_summary(self) -> None:
        """输出一次 Agent 请求的最终汇总日志。"""
        # TODO 3：记录 request_id、model_calls、tool_calls，
        # prompt_tokens、completion_tokens 和 total_tokens。
        logger.info(
            "Agent 请求完成 | request_id=%s | model_calls=%s | "
            "tool_calls=%s | prompt_tokens=%s | completion_tokens=%s | "
            "total_tokens=%s",
            self.request_id,
            self.model_calls,
            self.tool_calls,
            self.prompt_tokens,
            self.completion_tokens,
            self.total_tokens,
        )


def simulate_agent_run() -> AgentRunMetrics:
    """模拟两轮工具调用后，第三轮模型直接回答。"""
    metrics = AgentRunMetrics(request_id=uuid4().hex[:8])
    model_usages = [
        {"prompt_tokens": 120, "completion_tokens": 20, "total_tokens": 140},
        {"prompt_tokens": 180, "completion_tokens": 30, "total_tokens": 210},
        {"prompt_tokens": 240, "completion_tokens": 40, "total_tokens": 280},
    ]

    for round_number, usage in enumerate(model_usages, start=1):
        logger.info(
            "模型轮次完成 | request_id=%s | round=%s | total_tokens=%s",
            metrics.request_id,
            round_number,
            usage["total_tokens"],
        )
        metrics.record_model_usage(**usage)

        # 前两轮模型都要求调用工具，第三轮直接生成最终回答。
        if round_number < 3:
            metrics.record_tool_call()

    metrics.log_summary()
    return metrics


def main() -> None:
    configure_logging()
    simulate_agent_run()


if __name__ == "__main__":
    main()
