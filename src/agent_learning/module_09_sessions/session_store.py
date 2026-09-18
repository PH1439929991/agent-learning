"""第一节：按 session_id 存取独立的历史快照，只写两个 TODO。

纯内存、纯离线；不读取密钥、不请求模型、不写磁盘。
本节是存储层，不负责判断工具调用配对或回答是否正确。
"""

import json
from copy import deepcopy
from typing import Any


Message = dict[str, Any]


def validate_session_id(session_id: str) -> None:
    """已完成：ID 必须是非空字符串；保留原始 ID，不悄悄改写。"""
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id 必须是非空字符串")


class SessionStore:
    def __init__(self) -> None:
        # 每个 SessionStore 实例有自己的字典，不能定义为共享的类变量。
        self._histories: dict[str, list[Message]] = {}

    def load(self, session_id: str) -> list[Message]:
        """返回这段会话历史的深拷贝；不存在时返回新的空列表。"""
        validate_session_id(session_id)
        # TODO 1：用 self._histories.get(session_id, []) 取出历史，
        # 再用 deepcopy(...) 复制并返回。
        # 不要直接返回内部列表，也不要只用 .copy() 浅拷贝。
        return deepcopy(self._histories.get(session_id, []))

    def save(self, session_id: str, messages: list[Message]) -> None:
        """把完整历史的深拷贝保存到这个 ID 下，替换旧快照，不追加。"""
        validate_session_id(session_id)
        if not isinstance(messages, list) or any(not isinstance(m, dict) for m in messages):
            raise ValueError("messages 必须是由字典组成的列表")
        # TODO 2：self._histories[session_id] 保存 deepcopy(messages)。
        # 输入已经是完整历史；不能 extend，否则旧消息会重复。
        # 无需 return，也不应改变其他 session_id 对应的数据。
        self._histories[session_id] = deepcopy(messages)


def make_demo_history() -> list[Message]:
    """已完成：一轮成功工具问答的五条示例消息，不是真实模型输出。"""
    return [
        {"role": "system", "content": "只根据工具资料回答问题。"},
        {"role": "user", "content": "练习角色的旅伴叫什么？"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_demo_001", "type": "function", "function": {
                "name": "search_knowledge", "arguments": '{"query":"练习角色的旅伴"}'}}
        ]},
        {"role": "tool", "tool_call_id": "call_demo_001", "content": json.dumps({
            "success": True, "sources": [
                {"chunk_id": "demo_000", "text": "练习角色的旅伴是小星，来自示例地区。"}
            ]}, ensure_ascii=False)},
        {"role": "assistant", "content": "根据学习资料，旅伴是小星。[demo_000]"},
    ]


def main() -> None:
    store = SessionStore()
    try:
        store.save("session_A", make_demo_history())
        request_messages = store.load("session_A")
        request_messages.append({"role": "user", "content": "那小星来自哪里？"})
        print("A 下一轮准备使用的消息（尚未请求模型）：")
        print(json.dumps(request_messages, ensure_ascii=False, indent=2))
        print("临时请求消息数：", len(request_messages))
        print("A 已保存的历史消息数：", len(store.load("session_A")))
        print("B 的历史：", store.load("session_B"))
    except NotImplementedError as error:
        print(error)


if __name__ == "__main__":
    main()
