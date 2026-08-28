"""模型耗时与 Token 使用量练习。

目标：
1. 使用 dataclass 定义结构化返回结果。
2. 使用 perf_counter 记录模型调用耗时。
3. 从 response.usage 中读取输入、输出和总 Token。
4. 把完整回答加入上下文，而不是把整个结果对象加入上下文。
5. 连续对话多轮，观察 prompt_tokens 如何增长。

运行方式：
    python src/agent_learning/usage_metrics_exercise.py

这个文件是练习骨架，完成 TODO 前会主动抛出 NotImplementedError。
"""

from dataclasses import dataclass
from time import perf_counter

from LLM_client import LLMClient


SYSTEM_PROMPT = """你是一位耐心的 Python 编程导师。
回答要准确、简洁，并在不确定时明确说明。"""


@dataclass
class LLMResult:
    """一次完整模型调用的文本和统计信息。"""

    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    elapsed_seconds: float


def generate_with_metrics(
    llm: LLMClient,
    messages: list[dict[str, str]],
) -> LLMResult:
    """调用模型，并返回回答、Token 使用量和耗时。"""

    # TODO 1：调用 perf_counter()，记录请求开始时间。
    started_at = perf_counter()

    # TODO 2：使用 llm.client.chat.completions.create(...) 发起非流式请求。
    # 提示：需要传入 model、temperature 和 messages。
    # response = ...
    response = llm.client.chat.completions.create(
        model=llm.model,
        temperature=llm.temperature,
        messages=messages,
    )

    # TODO 3：再次调用 perf_counter()，用结束时间减去 started_at。
    # elapsed_seconds = ...
    elapsed_seconds = perf_counter() - started_at

    # TODO 4：从 response.choices[0].message.content 中取得回答。
    # 如果回答为空，抛出 RuntimeError。
    # content = ...
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("模型没有返回文本内容")

    # TODO 5：取得 response.usage。
    # usage = ...
    usage = response.usage or None
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.prompt_tokens + usage.completion_tokens if usage else 0
    # TODO 6：构造并返回 LLMResult。
    # 当 usage 为 None 时，可以暂时将 Token 数设置为 0。
    return LLMResult(
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        elapsed_seconds=elapsed_seconds,
    )



def print_result(result: LLMResult) -> None:
    """以容易观察的格式输出本轮调用结果。"""

    print(f"\n模型：{result.content}")
    print("\n--- 本轮统计 ---")
    print(f"输入 Token：{result.prompt_tokens}")
    print(f"输出 Token：{result.completion_tokens}")
    print(f"总 Token：{result.total_tokens}")
    print(f"总耗时：{result.elapsed_seconds:.2f} 秒")


def main(max_rounds: int = 5) -> None:
    llm = LLMClient()
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    cumulative_tokens = 0
    current_round = 0

    print("模型耗时与 Token 练习")
    print("输入 /exit 可以提前结束。")

    while current_round < max_rounds:
        try:
            user_input = input("\n用户：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n练习已结束")
            break

        if user_input.lower() in {"/exit", "exit", "quit", "退出"}:
            print("练习已结束")
            break

        if not user_input:
            print("输入不能为空")
            continue

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            result = generate_with_metrics(llm, messages)
        except Exception as error:
            # 请求失败时，撤销本轮尚未成功处理的用户消息。
            messages.pop()
            print(f"模型调用失败：{error}")
            continue

        messages.append(
            {
                "role": "assistant",
                "content": result.content,
            }
        )

        cumulative_tokens += result.total_tokens
        current_round += 1

        print_result(result)
        print(f"累计 Token：{cumulative_tokens}")
        print(f"当前轮数：{current_round}/{max_rounds}")


if __name__ == "__main__":
    main()
