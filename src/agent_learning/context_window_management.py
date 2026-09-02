"""上下文窗口管理练习骨架。

练习目标：
1. 人为设置一个较小的上下文窗口。
2. 估算 messages 使用的 Token 数。
3. 超过输入预算时，删除最早的完整 user + assistant 对话。
4. 始终保留 system 消息和当前用户的最新问题。

运行方式：
    python src/agent_learning/context_window_management.py

完成 TODO 前，程序会抛出 NotImplementedError。
"""

from math import ceil


Message = dict[str, str]

# 为了方便触发超限，这里故意把模拟窗口设置得很小。
SIMULATED_CONTEXT_LIMIT = 320
MAX_OUTPUT_TOKENS = 80
SAFETY_MARGIN = 20


class ContextWindowExceeded(RuntimeError):
    """已经没有历史消息可删，但最新消息仍然超过输入预算。"""


def estimate_messages_tokens(messages: list[Message]) -> int:
    """粗略估算整组消息占用的 Token 数。

    提示：
    - 中文字符可以暂时按照约 0.6 Token 估算。
    - 其他字符可以暂时按照约 0.3 Token 估算。
    - 每条消息可以额外增加少量格式开销。
    - 这里只用于练习，不要求与模型返回的 usage 完全一致。
    """

    total_tokens = 0.0
    message_format_overhead = 4

    for message in messages:
        content = message.get("content", "")

        chinese_count = sum(
            1 for char in content if "\u4e00" <= char <= "\u9fff"
        )
        other_count = len(content) - chinese_count

        total_tokens += chinese_count * 0.6
        total_tokens += other_count * 0.3
        total_tokens += message_format_overhead

    return ceil(total_tokens)


def trim_context(
    messages: list[Message],
    context_limit: int = SIMULATED_CONTEXT_LIMIT,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
    safety_margin: int = SAFETY_MARGIN,
) -> tuple[list[Message], list[Message]]:
    """将历史消息裁剪到输入预算以内。

    返回值：
        第一个列表：裁剪后保留的消息。
        第二个列表：本次被删除的历史消息。

    实现要求：
    - 不直接修改传入的 messages，先复制一份。
    - 第一条是 system 时始终保留。
    - 最后一条是当前 user 消息时始终保留。
    - 优先按照完整的 user + assistant 轮次删除。
    - 如果已经无历史可删，则抛出 ContextWindowExceeded。
    """

    # 输入预算 = 上下文窗口 - 最大输出 Token - 安全余量
    input_budget = context_limit - max_output_tokens - safety_margin

    copy_messages = messages.copy()
    removed_messages: list[Message] = []

    # 超过预算时，只从“可删除的历史区间”中删除消息。
    # 如果存在开头的 system 或末尾的当前 user，它们不在该区间内。
    while estimate_messages_tokens(copy_messages) > input_budget:
        history_start = (
            1
            if copy_messages and copy_messages[0].get("role") == "system"
            else 0
        )
        history_end = (
            len(copy_messages) - 1
            if copy_messages and copy_messages[-1].get("role") == "user"
            else len(copy_messages)
        )

        if history_start >= history_end:
            required_tokens = estimate_messages_tokens(copy_messages)
            raise ContextWindowExceeded(
                "没有可删除的历史消息："
                f"当前输入约 {required_tokens} Token，"
                f"输入预算为 {input_budget} Token。"
            )

        # 当最早的历史是 user + assistant 时，将它们作为完整轮次删除。
        remove_count = 1
        if (
            copy_messages[history_start].get("role") == "user"
            and history_start + 1 < history_end
            and copy_messages[history_start + 1].get("role") == "assistant"
        ):
            remove_count = 2

        removed_messages.extend(
            copy_messages[history_start : history_start + remove_count]
        )
        del copy_messages[history_start : history_start + remove_count]

    return copy_messages, removed_messages


def run_simulation(rounds: int = 8) -> None:
    """生成模拟多轮对话，用于检查你的裁剪逻辑。"""

    messages: list[Message] = [
        {
            "role": "system",
            "content": "你是一位耐心的 Python Agent 应用开发导师。",
        }
    ]

    print("上下文窗口管理模拟")
    print(f"模拟上下文窗口：{SIMULATED_CONTEXT_LIMIT} Token")

    for round_number in range(1, rounds + 1):
        messages.append(
            {
                "role": "user",
                "content": (
                    f"这是第 {round_number} 轮问题。"
                    + "请解释上下文窗口管理。" * 10
                ),
            }
        )

        messages, removed_messages = trim_context(messages)

        if removed_messages:
            removed_roles = ", ".join(
                message["role"] for message in removed_messages
            )
            print(
                f"第 {round_number} 轮：触发裁剪，"
                f"删除了 [{removed_roles}]"
            )
        else:
            print(f"第 {round_number} 轮：没有触发裁剪")

        # 固定文本用于模拟模型回答，不会真正调用 API。
        messages.append(
            {
                "role": "assistant",
                "content": "这是模型的模拟回答。" * 8,
            }
        )

        print(
            f"  当前约 {estimate_messages_tokens(messages)} Token，"
            f"保留 {len(messages)} 条消息"
        )


if __name__ == "__main__":
    run_simulation()
