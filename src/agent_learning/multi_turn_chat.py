from math import ceil

from LLM_client import LLMClient
from context_window_management import ContextWindowExceeded


def calculate_tokens(messages: list[dict[str, str]]) -> int:
    # 计算内容的token数量
    # 这里假设每个字符大约占用0.25个token，实际情况可能需要根据具体模型进行调整
    total_tokens = 0
    for message in messages:
        content = message.get("content", "")
        total_tokens += len(content) * 0.25
    return ceil(total_tokens)


def trim_context(
    history_content: list[dict[str, str]],
    max_tokens: int = 2048,
) -> list[dict[str, str]]:
    # 裁剪上下文，确保不超过最大token数
    current_history = history_content.copy()
    initial_tokens = calculate_tokens(current_history)
    print(f"初始token数量: {initial_tokens}")

    while calculate_tokens(current_history) > max_tokens:
        if len(current_history) <= 2:
            raise ContextWindowExceeded(
                "没有可删除的历史消息，"
                "但 system 和当前 user 仍然超过 Token 预算。"
            )

        if (
            current_history[1].get("role") != "user"
            or current_history[2].get("role") != "assistant"
        ):
            raise ContextWindowExceeded(
                "历史消息不是完整的 user + assistant 轮次。"
            )

        removed_messages = current_history[1:3]
        print("裁剪的角色内容：")
        for message in removed_messages:
            print(f'{message["role"]} - {message["content"]}')
        del current_history[1:3]

    removed_tokens = initial_tokens - calculate_tokens(current_history)
    print(f"总共裁剪了token数量: {removed_tokens}")
    return current_history


def multi_turn_chat(max_count: int = 10, max_tokens: int = 2048) -> None:
    # 初始化 LLM 客户端
    llm = LLMClient()
    system_message = {
        "role": "system",
        "content": "你是一个专业的助手，你的任务是回答用户的问题。",
    }

    # full_history 保留全部成功对话，content 只保留发给模型的近期上下文。
    full_history = [system_message]
    content = [system_message]
    current_count = 0

    while current_count < max_count:
        try:
            user_input = input("用户：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n对话已结束")
            break

        if user_input.lower() in {"/exit", "exit", "quit", "退出"}:
            print("对话已结束")
            break

        if not user_input:
            print("输入不能为空")
            continue

        current_user_message = {
            "role": "user",
            "content": user_input,
        }
        request_messages = [*content, current_user_message]

        try:
            request_messages = trim_context(request_messages, max_tokens)
            response = llm.generate(request_messages)
        except ContextWindowExceeded as error:
            print(f"上下文超限：{error}")
            continue
        except Exception as error:
            print(f"模型调用失败：{error}")
            continue

        assistant_message = {
            "role": "assistant",
            "content": response,
        }

        # 只有模型成功回答后，才更新完整历史和请求上下文。
        full_history.extend([current_user_message, assistant_message])
        content = [*request_messages, assistant_message]

        current_count += 1
        print(f"当前轮数：{current_count}/{max_count}")
        print(f"模型回复：{response}")


if __name__ == "__main__":
    multi_turn_chat()
