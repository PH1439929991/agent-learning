"""索引持久化离线练习用例：只使用 pytest 临时目录，不请求模型。"""

import json
from copy import deepcopy
from unittest.mock import Mock

import pytest

from agent_learning.module_08_rag import index_persistence as lesson


def sample():
    chunks = [{"chunk_id": "demo_000", "document_id": "demo", "text": "中文资料",
               "metadata": {"chunk_index": 0}}]
    payload = {"version": 1, "model": "test-model", "base_url": "https://example.invalid/v1/",
               "source_hash": lesson.source_fingerprint(chunks),
               "chunks": [{**chunks[0], "embedding": [0.6, 0.8]}]}
    return chunks, payload


def test_save_and_load(tmp_path):
    _, payload = sample()
    path = tmp_path / "nested" / "index.json"
    lesson.save_index(payload, path)
    assert lesson.load_index(path) == payload
    assert "中文资料" in path.read_text(encoding="utf-8")


def test_no_overwrite(tmp_path):
    _, payload = sample()
    path = tmp_path / "index.json"
    lesson.save_index(payload, path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        lesson.save_index({"different": True}, path)
    assert path.read_bytes() == before


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        lesson.load_index(tmp_path / "missing.json")


def test_invalid_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        lesson.load_index(path)


def test_valid_index():
    chunks, payload = sample()
    lesson.validate_index(payload, payload["model"], payload["base_url"], chunks)


@pytest.mark.parametrize("field", ["model", "base_url", "source_hash"])
def test_incompatible_index(field):
    chunks, payload = sample()
    modified = deepcopy(payload)
    modified[field] = "changed"
    with pytest.raises(ValueError):
        lesson.validate_index(modified, payload["model"], payload["base_url"], chunks)


def test_query_only_embeds_question(monkeypatch):
    chunks, payload = sample()
    client = Mock(base_url=payload["base_url"])
    monkeypatch.setattr(lesson, "load_index", Mock(return_value=payload))
    monkeypatch.setattr(lesson, "load_documents", Mock(return_value=[]))
    monkeypatch.setattr(lesson, "build_overlapping_chunks", Mock(return_value=chunks))
    monkeypatch.setattr(lesson, "create_embedding_client", Mock(return_value=(client, payload["model"])))
    fake_embed = Mock(return_value=[1.0, 0.0])
    fake_build = Mock(side_effect=AssertionError("查询不应重新建库"))
    monkeypatch.setattr(lesson, "embed_text", fake_embed)
    monkeypatch.setattr(lesson, "build_vector_index", fake_build)
    monkeypatch.setattr("sys.argv", ["lesson", "--query", "问题", "--live"])
    lesson.main()
    fake_embed.assert_called_once_with(client, payload["model"], "问题")
    fake_build.assert_not_called()
    client.close.assert_called_once_with()
