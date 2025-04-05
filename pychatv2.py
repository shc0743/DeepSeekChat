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
        response = requests.post(url, headers=headers, json=data, timeout=10)  # 设置超时时间为 10 秒
        response.raise_for_status()  # 检查 HTTP 状态码
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"API 调用失败: {e}")
        exit(1)

# 主函数
def main():
    api_key = read_api_key("skapikey.txt")

    # 预定义的提示词列表
    prompt_options = {
        "1": "You are a helpful assistant.",
        "2": "You are a developer.",
        "3": "You are a teacher."
    }

    # 显示提示词选项
    print("请选择系统提示词（输入编号或手动输入自定义提示词）：")
    for key, value in prompt_options.items():
        print(f"{key}. {value}")

    # 获取用户选择的提示词
    system_prompt = input("请输入编号或自定义提示词: ").strip()
    if system_prompt in prompt_options:
        system_prompt = prompt_options[system_prompt]
        print(f"使用提示词: {system_prompt}")
    else:
        print(f"使用自定义提示词: {system_prompt}")

    messages = initialize_messages(system_prompt)

    while True:
        user_message = input("你: ").strip()

        if user_message.lower() == "exit":
            print("对话结束。")
            break

        # 添加用户消息到对话历史
        messages.append({"role": "user", "content": user_message})

        try:
            # 获取助手的回复
            assistant_message = get_assistant_response(api_key, messages)
            print(f"助手: {assistant_message}")

            # 将助手的回复添加到对话历史
            messages.append({"role": "assistant", "content": assistant_message})
        except Exception as e:
            print(f"发生错误: {e}")
            continue  # 继续对话，而不是退出

if __name__ == "__main__":
    main()
