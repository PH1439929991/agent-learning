# RAG 学习总结与回家续学入口

整理日期：2026-09-15。覆盖最近两次学习、上次 GitHub 提交以来的第 5～10 节；按章节整理，不推断每节具体学习日期。

## 章节导航

| 章节 | 内容 | 当前状态 |
| --- | --- | --- |
| [第五节](05-真实Embedding.md) | 文本变向量、服务配置 | 已完成，并验证真实接口 |
| [第六节](06-TopK检索.md) | 建索引、相似度排序、Top-K | 已完成，9 个离线测试通过 |
| [第七节](07-索引保存与复用.md) | JSON 保存、加载、避免重复编码 | 已完成，9 个离线测试通过，并验证真实缓存查询 |
| [第八节](08-资料组装与回答.md) | 问题与正文组装为 messages | 已完成，10 个离线测试通过，未验证真实聊天回答 |
| [第九节](09-引用编号校验.md) | 引用编号提取与范围检查 | 已完成，14 个离线测试通过 |
| [第十节](10-生成与检查集成-待完成.md) | 返回原始答案和引用报告 | 框架已建，3 个 TODO 留待回家完成 |

前四节的切片、重叠、邻居扩展和余弦相似度可回顾[模块说明](../../src/agent_learning/module_08_rag/README.md)。

## 换电脑继续

在已有仓库的根目录先运行 `git status`，确认没有与远端冲突的未提交修改，再运行：

```bash
git pull --ff-only
```

新电脑尚无仓库时：

```bash
git clone https://github.com/PH1439929991/agent-learning.git
cd agent-learning
```

没有虚拟环境才创建，已有环境不用重复覆盖：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

虚拟环境不能直接跨电脑复制；环境一致不仅要 .env，还要 Python、依赖和代码版本一致。离线练习不需要配置密钥。

当前要写的文件是 [checked_rag_answer.py](../../src/agent_learning/module_08_rag/checked_rag_answer.py)，只写 answer_with_citation_check 的三个 TODO：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag/test_checked_rag_answer.py -q
```

未完成时这 6 个用例失败是预期，不是环境坏了。其他章节可单独验证：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_08_rag --ignore=src/agent_learning/module_08_rag/test_checked_rag_answer.py -q
```

预期 42 个通过。第十节完成后运行整个目录，应为 48 个通过。

## 不上传的文件与真实调用边界

- .env、.venv、本地 .cadk 数据不上传。
- work/rag_index*.json 被忽略，不会随着 git pull 下载。
- 旧模块六两处空行调整不属于本次提交，保留在原电脑。
- 新电脑要真实运行，需要自行配置 src/agent_learning/.env；不要把密钥发到聊天或提交 Git。
- 真正需要缓存时再按第七节重建，当前 14 段会产生 14 次 Embedding 请求，可能计费。离线完成第十节不需要索引。
- 英雄资料尚未事实核验；引用存在不等于答案正确。
