"""System Prompt 学习实验室。

运行方式：
    python src/agent_learning/system_prompt_lab.py

建议使用同一个问题依次切换不同 Prompt，比较回答的内容、结构和语气。
"""

from LLM_client import LLMClient


SYSTEM_PROMPTS = {
    "general": """你是一个有帮助的通用助手。
请准确回答用户问题；不确定时明确说明，不要编造信息。
回答使用简洁、自然的中文。""",
    "python_tutor": """你是一位耐心的 Python 编程导师，面向有后端基础的学习者。
先解释核心概念，再给出最小可运行示例。
指出常见错误和验证方法，但不要一次扩展太多无关知识。
如果用户的代码存在问题，先说明原因，再给出修改建议。""",
    "socratic_tutor": """你是一位使用苏格拉底方法教学的 Python 导师。
不要立即给出完整答案，优先提出一个能推动用户思考的关键问题。
根据用户回答逐步提供提示；当用户明确要求答案时，再给出完整解释。
每次最多提出两个问题。""",
    "code_reviewer": """你是一位严格但友善的 Python 代码审查员。
优先检查正确性、异常处理、安全性和可维护性。
先给出结论，再按严重程度列出问题，并给出最小修改建议。
没有发现问题时要明确说明，不要为了凑数量制造问题。""",
}


class SystemPromptLab:
    def __init__(self, prompt_name: str = "python_tutor") -> None:
        self.client = LLMClient()
        self.prompt_name = prompt_name
        self.system_prompt = self._get_prompt(prompt_name)
        self.messages: list[dict[str, str]] = []
        self.reset_history()

    def _get_prompt(self, prompt_name: str) -> str:
        try:
            return SYSTEM_PROMPTS[prompt_name]
        except KeyError as error:
            available = ", ".join(SYSTEM_PROMPTS)
            raise ValueError(
                f"未知 Prompt：{prompt_name}；可用选项：{available}"
            ) from error

    def reset_history(self) -> None:
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

    def use_prompt(self, prompt_name: str) -> None:
        self.system_prompt = self._get_prompt(prompt_name)
        self.prompt_name = prompt_name
        self.reset_history()

    def use_custom_prompt(self, prompt: str) -> None:
        if not prompt.strip():
            raise ValueError("自定义 System Prompt 不能为空")

        self.prompt_name = "custom"
        self.system_prompt = prompt.strip()
        self.reset_history()

    def chat(self, user_input: str) -> str:
        self.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            answer = self.client.generate(self.messages)
        except Exception:
            self.messages.pop()
            raise

        self.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )
        return answer


def print_help() -> None:
    print(
        """
可用命令：
  /prompts          查看预设 Prompt
  /use <名称>       切换预设 Prompt，并清空对话历史
  /custom <内容>    使用自定义 Prompt，并清空对话历史
  /show             查看当前 System Prompt
  /reset            清空历史，保留当前 System Prompt
  /help             查看帮助
  /exit             退出程序
""".strip()
    )


def main() -> None:
    lab = SystemPromptLab()

    print("System Prompt 学习实验室")
    print(f"当前 Prompt：{lab.prompt_name}")
    print_help()

    while True:
        try:
            user_input = input("\n用户：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n实验已结束")
            break

        if not user_input:
            continue

        if user_input == "/exit":
            print("实验已结束")
            break

        if user_input == "/help":
            print_help()
            continue

        if user_input == "/prompts":
            print("可用 Prompt：" + ", ".join(SYSTEM_PROMPTS))
            continue

        if user_input == "/show":
            print(f"当前 Prompt：{lab.prompt_name}")
            print(lab.system_prompt)
            continue

        if user_input == "/reset":
            lab.reset_history()
            print("对话历史已清空")
            continue

        if user_input.startswith("/use "):
            prompt_name = user_input.removeprefix("/use ").strip()
            try:
                lab.use_prompt(prompt_name)
            except ValueError as error:
                print(error)
            else:
                print(f"已切换到 {prompt_name}，对话历史已清空")
            continue

        if user_input.startswith("/custom "):
            prompt = user_input.removeprefix("/custom ")
            try:
                lab.use_custom_prompt(prompt)
            except ValueError as error:
                print(error)
            else:
                print("已使用自定义 Prompt，对话历史已清空")
            continue

        try:
            answer = lab.chat(user_input)
        except Exception as error:
            print(f"模型调用失败：{error}")
            continue

        print(f"模型：{answer}")


if __name__ == "__main__":
    main()
