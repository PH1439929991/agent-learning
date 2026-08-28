import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} 未配置")
    return value


class LLMClient:
    def __init__(self, temperature: float = 0.5) -> None:
        api_key = get_required_env("DEEPSEEK_API_KEY")
        base_url = get_required_env("DEEPSEEK_API_URL")
        self.model = get_required_env("DEEPSEEK_MODEL")
        self.temperature = temperature

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def generate(self, messages: list[dict[str,str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("模型没有返回文本内容")

        return content


if __name__ == "__main__":
    llm = LLMClient()
    print(llm.generate("你好"))
