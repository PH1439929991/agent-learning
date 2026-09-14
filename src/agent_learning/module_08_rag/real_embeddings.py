"""RAG 第五节：调用真实 Embedding 接口，得到文本向量。

只完成 embed_text() 的两个 TODO。默认运行只显示说明，不发送请求。
完成 TODO 并配置 .env 后，加 --live 会向配置的服务发送三句短文本，
正常完成共 3 次请求，可能产生费用；失败时停止，不自动重试。
本节不发送整个英雄资料库，不生成聊天回答，不保存向量到文件。

运行：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_08_rag.real_embeddings --live
官方 Python 接口参考：
    https://developers.openai.com/api/reference/python/resources/embeddings/methods/create
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agent_learning.module_08_rag.embedding_basics import cosine_similarity


def create_embedding_client() -> tuple[OpenAI, str]:
    """已完成：独立读取 Embedding 配置，不复用 DEEPSEEK_* 聊天配置。"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
    names = ("EMBEDDING_API_KEY", "EMBEDDING_BASE_URL", "EMBEDDING_MODEL")
    config = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise RuntimeError("请先在 .env 配置：" + ", ".join(missing))
    client = OpenAI(
        api_key=config["EMBEDDING_API_KEY"],
        base_url=config["EMBEDDING_BASE_URL"],
        timeout=20.0,
        max_retries=0,
    )
    # timeout 是网络操作超时配置，不是整段程序的严格总时限。
    return client, config["EMBEDDING_MODEL"]


def embed_text(client: OpenAI, model: str, text: str) -> list[float]:
    """把一段非空文本发给 Embedding 模型，返回一个浮点数列表。

    与聊天接口不同：输入是 input=text，不是 messages；不需要 system prompt。
    返回值是数字，不是 response.choices[0].message.content。
    """
    if not text.strip():
        raise ValueError("待编码文本不能为空或全是空白")

    raise NotImplementedError("请完成 embed_text 的两个 TODO")

    # TODO 1：调用 client.embeddings.create(...)，用 response 接收返回值。
    # 传入 model=model、input=text、encoding_format="float"。
    # model 是模型名称，input 是正文，float 表示返回浮点数格式的向量。

    # TODO 2：返回 response.data[0].embedding。
    # data 是结果列表；本次只传一段文本，所以取第 0 项中的 embedding。
    # 例如 [0.012, -0.034, ...]；真实维度和数字由模型决定，不要手填。


def run_comparison(client: OpenAI, model: str) -> None:
    """已完成：同一模型编码问题和两条候选文本，再按相似度排序。"""
    query = "我想了解亚索的背景故事。"
    candidates = ["关于亚索身世与经历的资料。", "如何烹饪意大利面。"]
    print("问题：", query)
    query_vector = embed_text(client, model, query)
    print("问题向量维度：", len(query_vector))
    print("问题向量前 5 个数：", query_vector[:5])

    results = []
    for text in candidates:
        vector = embed_text(client, model, text)
        score = cosine_similarity(query_vector, vector)
        results.append({"text": text, "score": score})
    results.sort(key=lambda result: result["score"], reverse=True)
    print("候选文本按相似度从高到低排列：")
    for result in results:
        print(f"{result['score']:.4f}  {result['text']}")
    # 不硬编码预期分数或排名：真实效果需要观察和评估，最高分不是正确率。


def main() -> None:
    parser = argparse.ArgumentParser(description="真实 Embedding 入门练习")
    parser.add_argument("--live", action="store_true", help="允许发送真实模型请求")
    args = parser.parse_args()
    if not args.live:
        print("请先完成 embed_text() 的两个 TODO，并配置 EMBEDDING_*。")
        print("加 --live 后会发送 3 句短文本，正常完成共 3 次请求，可能产生费用。")
        return

    client, model = create_embedding_client()
    try:
        run_comparison(client, model)
    finally:
        # 本函数创建的独立客户端，使用完后关闭；不是共享聊天客户端。
        client.close()


if __name__ == "__main__":
    main()
