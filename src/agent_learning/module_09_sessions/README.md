# 模块九：多轮 Agent 的会话状态

第八章的基础 RAG 已收尾。本章不重新讲切片、向量、工具注册，也暂不增加新框架。

计划集中完成三个主题：

1. 会话隔离与历史快照：不同 session_id 不串数据，工作副本不影响已保存状态（已完成，13 个测试通过）。
2. 连续追问与提交时机：读取历史，执行一轮 Agent，成功后保存完整的新历史；失败路径单独处理（已完成，16 个测试通过）。
3. 工具上下文的完整性：先检查工具调用与结果配对（当前），再学习完整轮次裁剪，最后做两轮问答验收。

当前入口：[第三节 A：工具消息配对检查](03-工具消息配对检查.md)。只填写 [tool_message_pairs.py](tool_message_pairs.py) 中的三个 TODO；测试与演示都不调用真实模型。前两节共 29 个测试通过，已完成的会话代码暂不接入这个未完成的检查器。

上一节回顾：[连续追问与成功后保存](02-连续追问与成功后保存.md)。

## 第一节：先做一个历史存储器

只改 [session_store.py](session_store.py) 中的 `SessionStore.load()`、`SessionStore.save()` 两个 TODO。[测试文件](test_session_store.py) 已准备好。本节纯离线，没有真实模型请求。

### 为什么第二章学过历史，还需要这一节？

第二章是一个聊天程序持有一份 history，主要处理 user、assistant 两种普通对话消息。现在要处理不同会话，以及 assistant.tool_calls、tool 这些嵌套数据。

第八章真实验收入口每次新建 messages，因此新一轮只传“那她来自哪里？”时，没有之前的对话可供模型参考。

我们采用手动维护历史的方式：应用读取对应会话的消息，再作为下一次请求的上下文。模型不会自动读取 Python 字典。这符合 OpenAI Docs 展示的手动管理对话状态方式；本章不改用其服务端 Conversations 接口。[官方 Conversation state 指南](https://developers.openai.com/api/docs/guides/conversation-state)

### 这里的 session_id 是什么？

它是应用用来区分一段会话的标识，例如 session_A、session_B。同一个人也可以有多段会话，它不是必然等于 user_id；也不是工具的 tool_call_id。

- session_A 可以聊练习角色。
- session_B 可以聊别的问题。
- load("session_A") 只取 A 的历史，不应该混入 B。

现在只是学习用 ID，不是权限凭据；真正对外提供服务还必须校验用户是否有权访问该会话。

### 输入、中间结果、输出

第一轮工具问答完成后，示例历史有五条消息：system、user、assistant 工具调用、tool 资料、assistant 最终答案。具体内容见代码中的 make_demo_history()。

```python
store.save("session_A", 已完成的五条消息)
request_messages = store.load("session_A")
request_messages.append({"role": "user", "content": "那小星来自哪里？"})
```

此时预期：

```python
len(request_messages)               # 6：本轮临时工作副本
len(store.load("session_A"))       # 5：已保存的快照还没变
store.load("session_B")            # []：新会话没有历史
```

本例保留 system 在完整历史中，下次读取时不要再重复添加一条 system。工具调用与结果都暂时原样保留，不在存储层擅自截断或总结。

### 为什么 load 和 save 都要 deepcopy？

列表里面还有字典，字典里可能还有 tool_calls 列表和 function 字典。

`messages.copy()` 只复制最外层列表，里面的字典仍然共享。修改其中的工具参数，可能连保存的历史一起改变。`deepcopy(messages)` 会为这些嵌套可变对象建立独立副本。

- save 时深拷贝：调用方之后修改原列表，不影响已保存历史。
- load 时深拷贝：本次处理问题时修改工作副本，不影响已保存历史。

这为“本轮失败时，不把未完成消息当成已完成历史”打基础。本节只提供存储能力，下一步才实现成功提交和失败路径；这不是完整的数据库事务，也不能撤销已经执行的外部工具副作用。

### 两个 TODO 怎么思考？

load：按 session_id 取列表，没找到用 []；返回它的深拷贝。

save：把传入的完整 messages 深拷贝后，赋值给这个 session_id。不要 extend，因为 messages 已包含旧历史，追加会重复。

`self._histories` 是当前 SessionStore 对象的内部字典。类的初始化、参数检查、演示都已写好，不需要改。

### 怎么运行？

在项目根目录执行：

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/agent_learning/module_09_sessions/test_session_store.py -q
PYTHONPATH=src .venv/bin/python -m agent_learning.module_09_sessions.session_store
```

第一节已完成，13 个测试全部通过。下方第二节继续接问答流程。演示数据是人为构造的，不表示模型已理解连续追问。

本节边界：只存内存、进程退出后丢失；不做工具协议校验、Token 裁剪、并发锁或持久化。不会修改前八章已完成的实现。
