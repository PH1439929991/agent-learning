"""第三节 A：检查工具消息配对。只填写 validate_tool_pairs 的三个 TODO。

纯离线；输入是序列化后的消息字典，不是 SDK 对象。
通过返回 None；不完整或配错抛出 ValueError；不修改输入。
"""

from copy import deepcopy

from agent_learning.module_09_sessions.session_store import Message, make_demo_history


def require_id(value) -> str:
    """已提供：ID 必须是非空字符串，保留原值，不擅自 strip 后配对。"""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("工具调用 ID 必须是非空字符串")
    return value


def validate_tool_pairs(messages: list[Message]) -> None:
    """校验完整工具消息块，而非工具执行到一半的临时状态。

    pending_ids：已经发起、还没收到结果的调用 ID 集合。
    同一批调用 ID 不允许重复；不同批次的 ID 是否重用不在本节检查范围。
    本函数不是完整的 API schema 校验器，也不检查最终回答是否存在。
    """
    if not isinstance(messages, list) or any(
        not isinstance(message, dict) for message in messages
    ):
        raise ValueError("messages 必须是消息字典列表")

    pending_ids: set[str] = set()

    for message in messages:
        role = message.get("role")

        if role == "tool":
            result_id = require_id(message.get("tool_call_id"))
            # TODO 2：收到结果，核销待办。
            # result_id 不在 pending_ids 中：raise ValueError("工具结果没有对应的待处理调用")。
            # 否则从 pending_ids 中 remove(result_id)。
            # 删除之后，相同 ID 的第二条结果就不能再次配对了。
            raise NotImplementedError("TODO 2：检查并移除结果对应的 ID")
            continue

        # 已提供：这一批工具尚未全部返回，不能插入其他角色消息。
        # 例如 assistant(call A) → user → tool(A)，虽然 ID 齐了，但顺序不对。
        if pending_ids:
            raise ValueError("工具结果未齐，不能插入非 tool 消息")

        if role == "assistant":
            calls = message.get("tool_calls")
            if calls is None:
                calls = []
            if not isinstance(calls, list) or any(
                not isinstance(call, dict) for call in calls
            ):
                raise ValueError("tool_calls 必须是字典列表")
            for call in calls:
                call_id = require_id(call.get("id"))
                # TODO 1：登记待办。
                # call_id 已在 pending_ids 中：raise ValueError("同一批工具调用 ID 重复")。
                # 否则把 call_id 加入 pending_ids，使用集合的 add()。
                raise NotImplementedError("TODO 1：检查并登记调用 ID")

    # TODO 3：遍历结束，pending_ids 非空说明仍然缺少工具结果。
    # 非空时 raise ValueError("缺少工具结果")；为空时正常结束（返回 None）。
    raise NotImplementedError("TODO 3：检查是否还有未返回的调用")


def main() -> None:
    normal = make_demo_history()
    orphan = deepcopy(normal)
    del orphan[2]  # 故意删除 assistant 的调用，保留 tool 结果。
    missing = normal[:3]  # 最后停在 assistant 工具调用，没有结果。
    duplicate = [*normal[:4], deepcopy(normal[3]), normal[4]]

    for title, messages in [
        ("正常配对", normal),
        ("孤立结果", orphan),
        ("缺少结果", missing),
        ("重复结果", duplicate),
    ]:
        try:
            result = validate_tool_pairs(messages)
        except NotImplementedError as error:
            print(f"{title}：尚未完成，{error}")
        except ValueError as error:
            print(f"{title}：已拦截，{error}")
        else:
            print(f"{title}：通过，返回值={result!r}")


if __name__ == "__main__":
    main()
