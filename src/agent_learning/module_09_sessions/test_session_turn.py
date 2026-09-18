"""第二节：真实会话存储 + 预设单轮执行器；不调用外部服务。"""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from agent_learning.module_09_sessions import session_turn as lesson
from agent_learning.module_09_sessions.session_store import SessionStore, make_demo_history


def test_two_turns_keep_tools_and_only_one_system():
    store = SessionStore()
    requests = []
    def run_turn(messages):
        requests.append(deepcopy(messages))
        # save 不能提前发生：执行第一轮时应为空，第二轮时仍是旧五条。
        assert len(store.load("A")) == (0 if len(requests) == 1 else 5)
        if len(requests) == 1:
            messages.extend(make_demo_history()[2:])
        else:
            messages.append({"role": "assistant", "content": "它来自示例地区。"})
        return messages
    answer1 = lesson.ask_with_history("A", "练习角色的旅伴叫什么？", store, run_turn)
    assert answer1 == make_demo_history()[-1]["content"]
    first_history = store.load("A")
    assert len(first_history) == 5
    answer2 = lesson.ask_with_history("A", "  那它来自哪里？  ", store, run_turn)
    assert answer2 == "它来自示例地区。"
    assert len(requests[0]) == 2
    assert requests[1] == [*first_history, {"role": "user", "content": "那它来自哪里？"}]
    assert len(store.load("A")) == 7
    assert sum(m["role"] == "system" for m in store.load("A")) == 1
    assert store.load("B") == []


@pytest.mark.parametrize("existing", [False, True])
def test_exception_never_saves_partial_history(existing):
    store = SessionStore()
    if existing:
        store.save("A", make_demo_history())
    before = store.load("A")
    store.save = Mock(wraps=store.save)
    def fail(messages):
        messages[0]["content"] = "被修改的临时副本"
        messages.append({"role": "assistant", "content": "半成品"})
        raise RuntimeError("模拟超时")
    runner = Mock(side_effect=fail)
    with pytest.raises(RuntimeError, match="模拟超时"):
        lesson.ask_with_history("A", "新问题", store, runner)
    runner.assert_called_once()
    store.save.assert_not_called()
    assert store.load("A") == before


@pytest.mark.parametrize("bad_result", [None, "仅有答案字符串", [],
    [{"role": "assistant", "content": "丢失原始请求"}]])
def test_invalid_result_never_saved(bad_result):
    store = SessionStore()
    store.save("A", make_demo_history())
    before = store.load("A")
    store.save = Mock(wraps=store.save)
    with pytest.raises(ValueError):
        lesson.ask_with_history("A", "新问题", store, Mock(return_value=bad_result))
    store.save.assert_not_called()
    assert store.load("A") == before


@pytest.mark.parametrize("last", [
    {"role": "assistant", "content": " "},
    {"role": "tool", "content": "还没结束", "tool_call_id": "unfinished"},
    {"role": "assistant", "content": "继续查", "tool_calls": [{"id": "unfinished"}]},
])
def test_unfinished_answer_never_saved(last):
    store = SessionStore()
    with pytest.raises(ValueError):
        lesson.ask_with_history("A", "问题", store, lambda messages: [*messages, last])
    assert store.load("A") == []


def test_runner_cannot_rewrite_existing_request():
    store = SessionStore()
    store.save("A", make_demo_history())
    before = store.load("A")
    def rewrite(messages):
        messages[2]["tool_calls"][0]["function"]["arguments"] = "被改写"
        return [*messages, {"role": "assistant", "content": "最终答案"}]
    with pytest.raises(ValueError, match="改写"):
        lesson.ask_with_history("A", "问题", store, rewrite)
    assert store.load("A") == before


def test_saved_result_does_not_share_runner_list():
    store = SessionStore()
    returned = []
    def run_turn(messages):
        returned.extend([*messages, {"role": "assistant", "content": "答案"}])
        return returned
    assert lesson.ask_with_history("A", "问题", store, run_turn) == "答案"
    returned[-1]["content"] = "执行器后来又改了数据"
    assert store.load("A")[-1]["content"] == "答案"


@pytest.mark.parametrize("question", [None, "", "  ", 123])
def test_invalid_question_never_runs(question):
    store, runner = SessionStore(), Mock()
    with pytest.raises(ValueError, match="question"):
        lesson.ask_with_history("A", question, store, runner)
    runner.assert_not_called()
    assert store.load("A") == []
