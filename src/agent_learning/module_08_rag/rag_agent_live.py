"""第十八节单次真实验收：模型选工具 → 检索一次 → 模型回答。

不是通用多轮 Agent：最多两次聊天、一次问题 Embedding，异常直接停止。
默认不联网；只有 --live 才执行。保留原第四章 Agent，不改全局注册表。
"""

import argparse
import json
from pathlib import Path

from agent_learning.module_08_rag.document_chunking import load_documents
from agent_learning.module_08_rag.index_persistence import DEFAULT_INDEX_PATH, load_index, validate_index
from agent_learning.module_08_rag.overlapping_chunking import build_overlapping_chunks
from agent_learning.module_08_rag.rag_live_acceptance import make_retrieve
from agent_learning.module_08_rag.rag_search_tool import (
    SYSTEM_PROMPT, SearchKnowledgeArguments, build_registration,
)
from agent_learning.module_08_rag.real_embeddings import create_embedding_client


DEFAULT_QUESTION = "根据学习资料，璐璐的仙灵旅伴叫什么？"


def run_agent_once(question, llm, retrieve, audit):
    """复用你写好的检索工具；第一次自动选工具，第二次要求结束作答。"""
    question = SearchKnowledgeArguments(query=question).query
    registry, tools = build_registration(retrieve)
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}]
    client = llm.client.with_options(timeout=20.0, max_retries=0)

    def request(tool_choice):
        # 仅是教学字符护栏，不是模型的真实 Token 计数。
        input_characters = len(json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False))
        if input_characters > 12000:
            raise ValueError("本次验收请求超过 12000 字符护栏")
        event = {"kind": "chat", "status": "started", "tool_choice": tool_choice,
                 "message_roles": [m["role"] for m in messages],
                 "input_characters": input_characters}
        audit.append(event)
        response = client.chat.completions.create(
            model=llm.model, messages=messages, tools=tools, tool_choice=tool_choice,
            temperature=llm.temperature, max_tokens=1024,
            extra_body={"thinking": {"type": "disabled"}},
        )
        event.update(status="responded", response_model=response.model,
                     usage=response.usage.model_dump() if response.usage is not None else None)
        if not response.choices:
            raise RuntimeError("模型没有返回 choices")
        choice = response.choices[0]
        event["finish_reason"] = choice.finish_reason
        if choice.finish_reason not in ("stop", "tool_calls"):
            raise RuntimeError("模型异常结束或输出截断，不自动重试")
        event["status"] = "completed"
        return choice

    first = request("auto")
    calls = first.message.tool_calls or []
    tool_result = None
    tool_call = None
    if calls:
        # 先检查全部调用数量，再执行，保证最多一次问题 Embedding。
        if len(calls) != 1 or first.finish_reason != "tool_calls":
            raise RuntimeError("本次验收只允许一个工具调用")
        call = calls[0]
        if call.type != "function" or call.function.name not in registry:
            raise ValueError("模型请求了未注册的工具")
        config = registry[call.function.name]
        arguments = json.loads(call.function.arguments)
        validated = config["arguments_model"].model_validate(arguments)
        tool_result = config["function"](**validated.model_dump())
        tool_call = call.model_dump()
        messages.append(first.message.model_dump(exclude_none=True))
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": json.dumps(tool_result, ensure_ascii=False)})
        final = request("none")
    else:
        final = first

    if final.finish_reason != "stop" or final.message.tool_calls:
        raise RuntimeError("最终回答仍要求工具调用，停止，不发第三次请求")
    answer = final.message.content
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("最终回答为空")
    return {"status": "answered_after_tool" if calls else "direct_answer",
            "question": question, "tool_call": tool_call, "tool_result": tool_result,
            "answer": answer, "messages": messages}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--index-file", type=Path, default=DEFAULT_INDEX_PATH)
    args = parser.parse_args()
    if not args.live:
        print("加 --live 验收一次真实问答：最多 2 次聊天 + 1 次问题 Embedding，可能计费。")
        print("不重建索引、不重试；第一次 tool_choice=auto，工具执行后 tool_choice=none。")
        return
    question = SearchKnowledgeArguments(query=args.question).query
    payload = load_index(args.index_file)
    chunks = build_overlapping_chunks(load_documents(), 300, 50)
    embedding_client, model = create_embedding_client()
    llm = None
    audit = []
    try:
        validate_index(payload, model, str(embedding_client.base_url), chunks)
        from agent_learning.common.llm_client import LLMClient
        llm = LLMClient()
        retrieve = make_retrieve(embedding_client, model, payload["chunks"], audit)
        print("开始单次验收；模型请求配置：", llm.model, flush=True)
        result = run_agent_once(question, llm, retrieve, audit)
        print(json.dumps({k: v for k, v in result.items() if k != "messages"},
                         ensure_ascii=False, indent=2), flush=True)
    finally:
        print("请求顺序与实际用量：", flush=True)
        print(json.dumps(audit, ensure_ascii=False, indent=2), flush=True)
        embedding_client.close()
        if llm is not None:
            llm.client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # 只输出错误类型/状态码，不打印第三方原始正文或密钥配置。
        print(f"验收停止：{type(error).__name__}，HTTP 状态={getattr(error, 'status_code', None)}")
        raise SystemExit(1) from None
