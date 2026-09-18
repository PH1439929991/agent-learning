"""第二节：读取历史 → 执行一轮 → 检查结果 → 成功后保存。

只填写 ask_with_history 的三个 TODO。本节不调用真实模型。
run_turn 接收消息列表，返回含最终 assistant 回答的完整消息列表。
"""

import json
from copy import deepcopy
from typing import Callable

from agent_learning.module_09_sessions.session_store import (
    Message, SessionStore, make_demo_history, validate_session_id,
)


SYSTEM_PROMPT = "只根据工具资料回答问题。"
RunTurn = Callable[[list[Message]], list[Message]]


def validate_completed_turn(request_messages: list[Message], completed_messages) -> None:
    """已完成：检查返回结构和最终文本，不判断事实，也不验证中间工具配对。

    本节约定 run_turn 只能追加新消息，不能改写已有请求。
    工具调用/结果的完整配对检查留到下一节。
    """
    if not isinstance(completed_messages, list) or any(
        not isinstance(message, dict) for message in completed_messages
    ):
        raise ValueError("本轮结果必须是消息字典列表")
    if len(completed_messages) <= len(request_messages):
        raise ValueError("本轮缺少新的最终回答")
    if completed_messages[:len(request_messages)] != request_messages:
        raise ValueError("本轮不能改写或丢失已有请求消息")
    final_message = completed_messages[-1]
    if final_message.get("role") != "assistant" or final_message.get("tool_calls"):
        raise ValueError("本轮必须以 assistant 最终回答结束")
    answer = final_message.get("content")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("最终回答必须是非空文本")


def ask_with_history(
    session_id: str, question: str, store: SessionStore, run_turn: RunTurn,
) -> str:
    """练习：成功才提交完整历史；异常向上传递，不伪装成功、不自动重试。

    store 为多轮共用的同一个对象，不要在函数内重新创建。
    run_turn 是程序传入的回调，不是让模型填写的参数。
    """
    validate_session_id(session_id)
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question 必须是非空字符串")
    question = question.strip()

    # TODO 1：用 store.load(session_id) 得到 request_messages。
    # 如果是空列表，先追加 {"role": "system", "content": SYSTEM_PROMPT}。
    # 然后追加本轮 {"role": "user", "content": question}，这里不要 save！
    try:
        request_messages = []
        session_history = store.load(session_id)
        if not session_history:
            session_history.append({"role": "system", "content": SYSTEM_PROMPT})
        session_history.append({"role": "user", "content": question})
        request_messages = deepcopy(session_history)
        # TODO 2：执行 completed_messages = run_turn(deepcopy(request_messages))。
        # run_turn 可能会原地追加消息，额外复制可保留请求原貌，供下面检查。
        # 调用 validate_completed_turn(request_messages, completed_messages)。
        completed_messages = run_turn(deepcopy(request_messages))
        validate_completed_turn(request_messages, completed_messages)
        # TODO 3：上面没有异常才执行 store.save(session_id, completed_messages)。
        # 最后返回 completed_messages[-1]["content"]。
        # 不要在 finally 中保存，不要仅保存最终答案，也不要再次追加 user。
        store.save(session_id, completed_messages)
        return completed_messages[-1]["content"]
    except Exception as error:
        raise error
    


def main() -> None:
    store = SessionStore()
    requests = []

    def fake_run_turn(messages):
        requests.append(deepcopy(messages))
        print(f"第 {len(requests)} 轮输入，共 {len(messages)} 条消息：")
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        if len(requests) == 1:
            # 第一轮预设工具调用、工具结果、最终回答；不是实际模型生成。
            return [*messages, *make_demo_history()[2:]]
        return [*messages, {"role": "assistant", "content": "根据学习资料，小星来自示例地区。[demo_000]"}]

    try:
        print("第一轮回答：", ask_with_history("A", "练习角色的旅伴叫什么？", store, fake_run_turn))
        print("第一轮后历史数：", len(store.load("A")))
        print("第二轮回答：", ask_with_history("A", "那它来自哪里？", store, fake_run_turn))
        print("第二轮后历史数：", len(store.load("A")))

        before = store.load("A")
        def failing_turn(messages):
            messages.append({"role": "assistant", "content": "未完成的临时内容"})
            raise RuntimeError("模拟本轮请求失败")
        try:
            ask_with_history("A", "继续介绍", store, failing_turn)
        except RuntimeError as error:
            print("第三轮错误：", error)
        print("失败后 A 的历史未改变：", store.load("A") == before)
        print("B 的历史：", store.load("B"))
    except NotImplementedError as error:
        print(error)


if __name__ == "__main__":
    main()
