"""第六节离线检查：不读取密钥、不请求真实模型，TODO 未完成时会失败。"""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from agent_learning.module_08_rag import top_k_retrieval as lesson


def make_index():
    # 故意把低分片段放在前面，防止未排序就直接截取。
    return [
        {"chunk_id": "other_000", "text": "其他资料", "embedding": [0.0, 1.0]},
        {"chunk_id": "yasuo_000", "text": "资料甲", "embedding": [1.0, 0.0]},
        {"chunk_id": "yasuo_001", "text": "资料乙", "embedding": [0.8, 0.6]},
    ]


@pytest.mark.parametrize("top_k, expected", [
    (1, ["yasuo_000"]),
    (2, ["yasuo_000", "yasuo_001"]),
    (10, ["yasuo_000", "yasuo_001", "other_000"]),
])
def test_top_k(top_k, expected):
    index = make_index()
    before = deepcopy(index)
    hits = lesson.search_top_k([1.0, 0.0], index, top_k)
    assert [hit["chunk"]["chunk_id"] for hit in hits] == expected
    assert [hit["score"] for hit in hits] == pytest.approx([1.0, 0.8, 0.0][:len(expected)])
    assert all(hit["chunk"] in index for hit in hits)
    assert index == before


def test_empty_index():
    assert lesson.search_top_k([1.0, 0.0], [], 3) == []


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_invalid_k(top_k):
    with pytest.raises(ValueError, match="正整数"):
        lesson.search_top_k([1.0, 0.0], make_index(), top_k)


def test_build_index(monkeypatch):
    chunks = [{"chunk_id": "demo_000", "text": "原文", "metadata": {"chunk_index": 0}}]
    before = deepcopy(chunks)
    fake_embed = Mock(return_value=[0.6, 0.8])
    monkeypatch.setattr(lesson, "embed_text", fake_embed)
    client = object()
    index = lesson.build_vector_index(client, "test-model", chunks)
    fake_embed.assert_called_once_with(client, "test-model", "原文")
    assert index == [{**chunks[0], "embedding": [0.6, 0.8]}]
    assert chunks == before
    assert index[0] is not chunks[0]
