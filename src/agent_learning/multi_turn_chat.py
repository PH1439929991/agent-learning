

from LLM_client import LLMClient

def multi_turn_chat(maxCount:int=10):
    #初始化LLM客户端
    llm = LLMClient()
    #历史内容
    history_content = []
    #最大轮数
    maxCount = maxCount;


    #当前轮数
    currentCount = 0
    while currentCount < maxCount:
        #用户输入
        try:
            user_input = input("用户：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n对话已结束")
            break

        #跳出逻辑
        if user_input.lower() in {"/exit", "exit", "quit", "退出"}:
            print("对话已结束")
            break

        history_content.append({"role": "user", "content": user_input})
        #模型回复
        response = llm.generate(history_content)
        #更新历史内容
        history_content.append({"role": "assistant", "content": response})
        #打印当前轮数
        print(f"当前轮数：{currentCount+1}/{maxCount}")
        #打印模型回复
        print(f"模型回复：{response}")
        #更新当前轮数
        currentCount += 1


if __name__ == "__main__":
    multi_turn_chat()
