import json
import os
import requests

# 从 skapikey.txt 文件中读取 API Key
def read_api_key(file_path):
    try:
        with open(file_path, 'r') as file:
            api_key = file.read().strip()
            if not api_key:
                raise ValueError("API Key 未找到或为空")
            return api_key
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
        exit(1)
    except Exception as e:
        print(f"读取 API Key 时出错: {e}")
        exit(1)

# 初始化对话历史
def initialize_messages(system_prompt):
    return [
        {"role": "system", "content": system_prompt}
    ]

# 对用户输入的内容进行 JSON 转义
def escape_message(message):
    return message.replace('"', '\\"').replace('\\', '\\\\')

# 调用 API 获取助手的回复
def get_assistant_response(api_key, messages):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "stream": False
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"API 调用失败: {e}")
        exit(1)

# 主函数
def main():
    api_key = read_api_key("skapikey.txt")

    # 允许用户设置提示词
    system_prompt = input("请输入系统提示词（直接按回车使用默认提示词）: ").strip()
    if not system_prompt:
        system_prompt = "You are a helpful assistant."
        print(f"使用默认提示词: {system_prompt}")

    messages = initialize_messages(system_prompt)

    while True:
        user_message = input("你: ").strip()

        if user_message.lower() == "exit":
            print("对话结束。")
            break

        # 转义用户输入并添加到对话历史
        escaped_message = escape_message(user_message)
        messages.append({"role": "user", "content": escaped_message})

        # 获取助手的回复
        assistant_message = get_assistant_response(api_key, messages)
        print(f"助手: {assistant_message}")

        # 将助手的回复添加到对话历史
        messages.append({"role": "assistant", "content": assistant_message})

if __name__ == "__main__":
    main()
