import json
import os
import ctypes
import requests
import platform

# 您也可以选择嵌入式 api key
CONFIG_APIKEY = "PASTE_YOUR_API_KEY_HERE"

# 从 skapikey.txt 文件中读取 API Key
def read_api_key(file_path):
    if CONFIG_APIKEY != "PASTE_YOUR_API_KEY_HERE":
        return CONFIG_APIKEY
        # 虽然可能不是最佳实践，我们允许嵌入式开发者在代码中嵌入 API Key 。
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
        "stream": True  # 启用流式响应
    }
    try:
        # 使用流式请求
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=90)
        response.raise_for_status()

        # 逐步处理流式响应
        assistant_message = ""
        print("助手: ", end="", flush=True)  # 设置助手回复为绿色
        try:
            for line in response.iter_lines():
                if line:
                    # 解码每一行
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line == "data: [DONE]":  # 处理结束标记
                        print("")  # 重置颜色并换行
                        break
                    if decoded_line.startswith("data:"):
                        try:
                            event_data = json.loads(decoded_line[5:])  # 去掉 "data:" 前缀
                            if "choices" in event_data and len(event_data["choices"]) > 0:
                                delta = event_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    assistant_message += delta["content"]
                                    print(delta["content"], end="", flush=True)  # 逐步显示助手的回复
                        except json.JSONDecodeError as e:
                            print(f"解析 JSON 时出错: {e}")
                            continue  # 跳过无效数据
        except KeyboardInterrupt:
            print("\n\n\033[91m用户中断\033[0m")  # 提示用户已中断
            return assistant_message  # 返回已生成的部分内容

        return assistant_message  # 返回完整的助手回复
    except requests.exceptions.RequestException as e:
        print(f"提供方调用异常: {e}")
        return f"提供方调用异常: {e}"

# 保存对话历史到文件
def save_conversation(messages, filename):
    try:
        if not filename:
            raise ValueError("文件名不能为空")
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)
        print(f"对话历史已保存到文件: {filename}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

def load_conversation(filename):
    try:
        if not filename:
            raise ValueError("文件名不能为空")
        with open(filename, 'r', encoding='utf-8') as file:
            messages = json.load(file)
            # print(f"对话历史已从文件 {filename} 加载。")
            return messages
    except FileNotFoundError:
        print(f"文件 {filename} 未找到。")
    except Exception as e:
        print(f"加载文件时出错: {e}")
    return None

def load_conversation_handler(filename, messages):
    if not filename:
        print("错误：未指定文件名。")
        return True
    new_messages = load_conversation(filename)
    if new_messages:
        if messages and len(messages) > 1:  # 如果当前有对话历史
            choice = input("当前已有对话历史，是否覆盖？(y/N): ").strip().lower()
            if choice != 'y':
                print("取消加载。")
                return True
        messages.clear()
        messages.extend(new_messages)
        print("对话历史已加载并覆盖当前对话。")

        # 询问是否打印历史对话上下文
        print_choice = input("是否将历史对话上下文打印到控制台？(y/N): ").strip().lower()
        if print_choice == 'y':
            print("\n=== 历史对话上下文 ===")
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    print(f"\033[36m你: {content}\033[0m")
                elif role == "assistant":
                    print(f"助手: {content}")
                elif role == "system":
                    print(f"\033[33m系统提示: {content}\033[0m")
            print("=====================\n")
    return True

def clear_screen():
    print("\033[2J\033[H", end="", flush=True)

def handle_user_command(command, messages):
    # 命令处理函数字典
    command_handlers = {
        "exit": lambda: (print("对话结束。"), False),  # 返回 False 表示结束对话
        "save": lambda: (save_conversation(messages, command[len("save "):].strip()), True),  # 返回 True 表示继续对话
        "clear": lambda: (messages.clear(), messages.append({"role": "system", "content": system_prompt}), print("对话历史已清空。"), True),  # 清空对话历史并重置系统提示
        "load": lambda: (load_conversation_handler(command[len("load "):].strip(), messages), True),  # 加载对话历史
        "cls": lambda: (clear_screen(), True)  # 清屏命令
    }
    # 命令说明字典
    command_docs = {
        "exit": "退出程序。",
        "save": "保存当前对话历史到文件。用法: /save <文件名>",
        "clear": "清空当前对话历史并重置系统提示。",
        "load": "从文件加载对话历史。用法: /load <文件名>",
        "cls": "清屏。",
        "help": "显示所有可用命令及其说明。"
    }
    # 单独处理 /help 命令
    if command == "help":
        print("\033[35m=== 可用命令 ===\033[0m")
        for cmd, doc in command_docs.items():
            print(f"/{cmd}: {doc}")
        print("\033[35m================\033[0m")
        return True

    # 提取命令名称
    command_name = command.split()[0] if command else ""
    if command_name not in command_handlers:
        print("\033[35m错误：未知命令。输入 /help 以查看可用命令列表。\033[0m")
        return True  # 继续对话

    # 调用对应的命令处理函数
    print('\033[35m', end='')
    result = command_handlers[command_name]()
    print('\033[0m', end='')
    if isinstance(result, tuple):  # 如果返回的是元组，取最后一个值
        return result[-1]
    return result

# 预定义的提示词列表
prompt_options = {
    "0": "退出程序",
    "1": "You are a helpful assistant.",
    "2": "You are a software developer.",
    "3": "You are a helpful assistant. The user is a Chinese user, so reply in Chinese, unless the user obviously asks you to reply in other languages."
}

def main():
    global system_prompt  # 将 system_prompt 声明为全局变量，以便在 handle_user_command 中使用
    api_key = read_api_key("skapikey.txt")

    # 显示提示词选项
    print("请选择系统提示词（输入编号或手动输入自定义提示词）：")
    for key, value in prompt_options.items():
        print(f"{key}. {value}")

    # 获取用户选择的提示词
    system_prompt = input("请输入编号或自定义提示词: ").strip()
    if system_prompt == '0':
        exit(0)
    if not system_prompt:
        system_prompt = prompt_options['1']
    if system_prompt in prompt_options:
        system_prompt = prompt_options[system_prompt]
        print(f"使用提示词: {system_prompt}")
    else:
        print(f"使用自定义提示词: {system_prompt}")

    messages = initialize_messages(system_prompt)

    while True:
        user_message = input("\033[36m你: ").strip()
        print("\033[0m", end='')

        # 处理斜杠命令
        if user_message.startswith('/'):
            if not handle_user_command(user_message[1:], messages):  # 去掉斜杠并处理命令
                break
            continue  # 跳过后续逻辑，继续等待用户输入

        # 添加用户消息到对话历史
        messages.append({"role": "user", "content": user_message})

        try:
            # 获取助手的回复
            assistant_message = get_assistant_response(api_key, messages)
            #print(f"助手: {assistant_message}")

            # 将助手的回复添加到对话历史
            messages.append({"role": "assistant", "content": assistant_message})
        except Exception as e:
            print(f"调用提供程序时发生错误: {e}")
            continue  # 继续对话，而不是退出
    print("正在退出。")


if __name__ == "__main__":
    main()
