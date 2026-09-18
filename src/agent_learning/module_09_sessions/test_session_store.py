"""会话快照练习；不联网。两个 TODO 完成后目标为 13 个用例通过。"""

from copy import deepcopy

import pytest

from agent_learning.module_09_sessions.session_store import SessionStore, make_demo_history


def test_new_session_is_empty():
    store = SessionStore()
    assert store.load("new") == []


def test_round_trip_preserves_all_tool_messages():
    store = SessionStore()
    history = make_demo_history()
    store.save("A", history)
    assert store.load("A") == history
    assert [m["role"] for m in store.load("A")] == ["system", "user", "assistant", "tool", "assistant"]


def test_sessions_do_not_mix():
    store = SessionStore()
    store.save("A", make_demo_history())
    other = [{"role": "user", "content": "另一段会话"}]
    store.save("B", other)
    assert store.load("A") == make_demo_history()
    assert store.load("B") == other


def test_save_copies_nested_objects():
    store = SessionStore()
    original = make_demo_history()
    expected = deepcopy(original)
    store.save("A", original)
    original[2]["tool_calls"][0]["function"]["name"] = "被外部改动"
    original.append({"role": "user", "content": "不应自动进入历史"})
    assert store.load("A") == expected


def test_load_returns_independent_working_copy():
    store = SessionStore()
    store.save("A", make_demo_history())
    working = store.load("A")
    working[2]["tool_calls"][0]["function"]["arguments"] = "被外部改动"
    working.append({"role": "user", "content": "尚未完成的新问题"})
    assert store.load("A") == make_demo_history()


def test_save_replaces_full_snapshot_without_duplication():
    store = SessionStore()
    store.save("A", make_demo_history())
    updated = store.load("A")
    updated.extend([{"role": "user", "content": "谢谢"},
                    {"role": "assistant", "content": "不客气"}])
    store.save("A", updated)
    assert store.load("A") == updated
    assert len(store.load("A")) == 7


def test_store_instances_are_independent():
    first, second = SessionStore(), SessionStore()
    first.save("A", make_demo_history())
    assert second.load("A") == []


@pytest.mark.parametrize("bad_id", [None, "", "  "])
def test_invalid_session_id(bad_id):
    store = SessionStore()
    with pytest.raises(ValueError, match="session_id"):
        store.load(bad_id)
    with pytest.raises(ValueError, match="session_id"):
        store.save(bad_id, [])


@pytest.mark.parametrize("bad_messages", [None, {}, ["不是字典"]])
def test_invalid_history_type(bad_messages):
    with pytest.raises(ValueError, match="messages"):
        SessionStore().save("A", bad_messages)
