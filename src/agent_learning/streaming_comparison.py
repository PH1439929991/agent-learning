"""对比模型的非流式输出和流式输出。

运行方式：
    python src/agent_learning/streaming_comparison.py

也可以传入自己的问题：
    python src/agent_learning/streaming_comparison.py "请解释 Python 生成器"

注意：一次完整运行会向模型发送两次请求，分别用于非流式和流式测试。
"""

import argparse
from time import perf_counter

from LLM_client import LLMClient


DEFAULT_PROMPT = """请用 8 个简短步骤解释：
当我在浏览器输入一个网址并按下回车后，一个 HTTP 请求如何到达服务端，
服务端的响应又如何回到浏览器。每个步骤单独一行。"""

SYSTEM_PROMPT = """你是一位面向后端开发者的技术讲解员。
使用准确、容易理解的中文回答，并严格遵守用户要求的输出结构。"""


def build_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]


def run_non_stream(
    llm: LLMClient,
    messages: list[dict[str, str]],
) -> str:
    print("\n========== 非流式输出 ==========")
    print("请求已经发出，正在等待完整回答……")

    started_at = perf_counter()
    response = llm.client.chat.completions.create(
        model=llm.model,
        temperature=llm.temperature,
        messages=messages,
    )
    total_seconds = perf_counter() - started_at

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("非流式请求没有返回文本内容")

    # 调用结束以后，才会一次性执行到这里并打印完整回答。
    print("\n模型回答：")
    print(content)
    print(f"\n非流式总耗时：{total_seconds:.2f} 秒")
    print("非流式首段可见时间：等于总耗时")
    return content


def run_stream(
    llm: LLMClient,
    messages: list[dict[str, str]],
) -> str:
    print("\n========== 流式输出 ==========")
    print("模型回答：")

    started_at = perf_counter()
    stream = llm.client.chat.completions.create(
        model=llm.model,
        temperature=llm.temperature,
        messages=messages,
        stream=True,
    )

    content_parts: list[str] = []
    first_content_seconds: float | None = None

    # 这里是流式响应的接收循环：每到达一个 chunk，就立即处理一次。
    for chunk in stream:
        if not chunk.choices:
            continue

        content = chunk.choices[0].delta.content
        if not content:
            continue

        if first_content_seconds is None:
            first_content_seconds = perf_counter() - started_at

        print(content, end="", flush=True)
        content_parts.append(content)

    total_seconds = perf_counter() - started_at
    full_content = "".join(content_parts)

    if not full_content:
        raise RuntimeError("流式请求没有返回文本内容")

    if first_content_seconds is None:
        raise RuntimeError("没有记录到首段响应时间")

    print()
    print(f"\n流式首段可见时间：{first_content_seconds:.2f} 秒")
    print(f"流式总耗时：{total_seconds:.2f} 秒")
    return full_content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用同一个问题对比非流式输出和流式输出。"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="需要发送给模型的问题；省略时使用内置的 HTTP 请求示例。",
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="非流式请求完成后，不等待按 Enter，直接开始流式请求。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    llm = LLMClient()
    messages = build_messages(args.prompt)

    print("本程序会使用同一个问题调用模型两次。")
    print("第一次等待完整回答，第二次边生成边显示。")
    print(f"\n测试问题：\n{args.prompt}")

    try:
        run_non_stream(llm, messages)

        if not args.no_pause:
            input("\n按 Enter 开始流式输出测试……")

        run_stream(llm, messages)
    except (KeyboardInterrupt, EOFError):
        print("\n测试已取消")
    except Exception as error:
        print(f"\n模型调用失败：{error}")


if __name__ == "__main__":
    main()
