# import os
# from google import genai
#
# # 设置环境变量
# os.environ["GOOGLE_API_KEY"] = "AIzaSyBUpSEfFRLyy3kb3dH6wKtsziBRtgytaw0"
#
# # The client gets the API key from the environment variable `GEMINI_API_KEY`.
# client = genai.Client()
#
# response = client.models.generate_content(
#     model="gemini-2.5-flash", contents="when do you last upgrade your data"
# )
# print(response.text)

# from openai import OpenAI
#
# def call_llm(messages):
#     # 初始化客户端
#     client = OpenAI(
#         api_key="lm-studio",
#         base_url="http://localhost:1234/v1",
#     )
#
#     stream = client.chat.completions.create(
#         model="deepseek/deepseek-r1-0528-qwen3-8b",
#         messages=messages,
#         # 超参数
#         temperature=0.7,  # 控制输出的随机性，值越低输出越确定
#         top_p=0.9,  # 控制输出的多样性，值越低输出越集中
#         max_tokens=5120,  # 控制生成的最大token数量
#         frequency_penalty=0.5,  # 减少重复内容的生成
#         presence_penalty=0.5,  # 鼓励模型引入新内容
#         stream=True  # 启用流式输出
#     )
#
#     full_response = []
#     print("AI助手: ", end="", flush=True)
#     for chunk in stream:
#         if chunk.choices[0].delta.content:
#             content = chunk.choices[0].delta.content
#             print(content, end="", flush=True)  # 流式输出
#             full_response.append(content)
#     print("\n")
#     return "".join(full_response)
#
#
# if __name__ == "__main__":
#     # 初始化对话历史，包含系统消息
#     messages = [
#         {"role": "system", "content": "你是一个有用的助手"}
#     ]
#
#     while True:
#         # 获取用户输入
#         user_input = input("\n用户: ")
#         if user_input.lower() in ["exit", "quit", "再见"]:  # 输入"exit"、"quit"或“再见”退出程序
#             break
#
#         # 添加用户消息到历史
#         messages.append({"role": "user", "content": user_input})
#
#         # 调用模型并获取响应
#         assistant_response = call_llm(messages)
#
#         # 添加助手响应到历史
#         messages.append({"role": "assistant", "content": assistant_response})

from openai import OpenAI


def call_llm(messages):
    # 初始化客户端
    # Ollama 默认运行在 11434 端口
    # OpenAI 兼容模式的地址通常为 http://localhost:11434/v1
    client = OpenAI(
        api_key="ollama",  # Ollama 不需要真实的 key，但这必须是非空字符串
        base_url="http://localhost:11434/v1",
    )

    try:
        stream = client.chat.completions.create(
            model="llama3.1:latest",  # 修改为你本地 Ollama 中的模型名称
            messages=messages,
            # 超参数
            temperature=0.7,
            top_p=0.9,
            max_tokens=5120,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stream=True
        )

        full_response = []
        print("AI助手: ", end="", flush=True)
        for chunk in stream:
            # 兼容性处理：有些模型返回的 delta 可能为空
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response.append(content)
        print("\n")
        return "".join(full_response)

    except Exception as e:
        print(f"\n发生错误: {e}")
        return ""


if __name__ == "__main__":
    # 初始化对话历史
    messages = [
        {"role": "system", "content": "你是一个有用的助手"}
    ]

    print("--- 已连接到本地 Ollama (Llama 3.1) ---")

    while True:
        try:
            user_input = input("\n用户: ")
            if not user_input:  # 处理空输入
                continue

            if user_input.lower() in ["exit", "quit", "再见"]:
                break

            messages.append({"role": "user", "content": user_input})

            assistant_response = call_llm(messages)

            # 只有在成功获取响应后才添加到历史记录
            if assistant_response:
                messages.append({"role": "assistant", "content": assistant_response})

        except KeyboardInterrupt:
            print("\n程序已退出。")
            break
