import json
import os
import ctypes
import requests
import platform
import time
import sys
from ctypes import wintypes

# 您也可以选择嵌入式 api key
CONFIG_APIKEY = "PASTE_YOUR_API_KEY_HERE"

# 从 skapikey.txt 文件中读取 API Key，如果没有则提示用户输入
def read_api_key(file_path):
    global CONFIG_APIKEY
    # 如果代码中嵌入了 API Key，则直接使用
    if CONFIG_APIKEY != "PASTE_YOUR_API_KEY_HERE":
        return CONFIG_APIKEY

    try:
        # 尝试从文件中读取 API Key
        with open(file_path, 'r') as file:
            api_key = file.read().strip()
            if not api_key:
                raise ValueError("API Key 未找到或为空")
            CONFIG_APIKEY = api_key
            return api_key
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except Exception as e:
        print(f"读取 API Key 时出错: {e}")

    # 如果没有找到 API Key，提示用户输入
    api_key = input("请输入您的 API Key: ").strip()
    if not api_key:
        print("错误：API Key 不能为空。")
        exit(1)

    CONFIG_APIKEY = api_key
    return api_key

# 检测 API Key 是否有效，并打印账户余额
def check_api_account(api_key):
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 401:
            print(f"\033[91m错误：API Key 无效。Secret: {api_key}\033[0m")
            return False
        response.raise_for_status()  # 检查其他 HTTP 错误

        # 解析响应数据
        data = response.json()
        if data.get("is_available", False):
            balance_infos = data.get("balance_infos", [])
            if balance_infos:
                for balance in balance_infos:
                    currency = balance.get("currency", "未知")
                    total_balance = balance.get("total_balance", "0.00")
                    granted_balance = balance.get("granted_balance", "0.00")
                    topped_up_balance = balance.get("topped_up_balance", "0.00")
                    print(f"\033[32m当前余额{total_balance}{currency} (充值余额 {topped_up_balance}{currency}，赠送余额 {granted_balance}{currency})\033[0m")
            else:
                print("\033[92m账户余额信息为空。\033[0m")
            return True
        else:
            print("\033[91m错误：余额不足。\033[0m")
            time.sleep(2)
            return False
    except requests.exceptions.RequestException as e:
        print(f"\033[91m检测账户时出错: {e}\033[0m")
        return False

def enable_vt_mode():
    """
    在 Windows 上启用虚拟终端模式
    """
    if not sys.platform.startswith('win'):
        # 如果不是 Windows 系统，直接返回
        return

    # 定义常量
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    # 获取标准输出句柄
    kernel32 = ctypes.windll.kernel32
    h_out = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    
    # 获取当前控制台模式
    mode = wintypes.DWORD()
    kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
    
    # 启用虚拟终端模式
    mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
    kernel32.SetConsoleMode(h_out, mode)

# 全局参数字典
global_params = {
    "context_limit": 20,  # 默认上下文消息数量上限
    "skip_account_check": False, # 启动时不进行APIKEY检查
    "model": "deepseek-chat",  # 默认模型
}

# 获取参数值的函数
def get_param(key=None):
    if key:
        return global_params.get(key, "参数不存在")
    return global_params

# 读取 preferences.json 文件并加载到 global_params
def load_preferences():
    try:
        with open("preferences.json", 'r') as file:
            preferences = json.load(file)
            global_params.update(preferences)
            #print("参数已从 preferences.json 加载。")
    except FileNotFoundError:
        #print("preferences.json 文件未找到，将使用默认参数。")
        pass
    except Exception as e:
        print(f"加载 preferences.json 时出错: {e}")
        pass

# 保存单个参数到 preferences.json 文件
def save_preference(key, value):
    try:
        # 读取现有的 preferences.json 文件（如果存在）
        try:
            with open("preferences.json", 'r') as file:
                preferences = json.load(file)
        except FileNotFoundError:
            preferences = {}

        # 更新指定的键值对
        preferences[key] = value

        # 保存更新后的 preferences.json 文件
        with open("preferences.json", 'w') as file:
            json.dump(preferences, file, indent=4)
            print(f"\033[92m√ 已保存 \033[35m", end='')
    except Exception as e:
        print(f"\033[91m! 无法保存 \033[35m", end='')

# 修改 set_param 函数以支持保存单个参数到 preferences.json
def set_param(key, value, save_to_file=True):
    #print('          ', end='')
    try:
        # 首先尝试解析为整数
        global_params[key] = int(value)
    except ValueError:
        try:
            # 如果整数解析失败，尝试解析为布尔值
            if value.lower() in ["true", "false"]:
                global_params[key] = value.lower() == "true"
            else:
                # 如果布尔值解析失败，保存为字符串
                global_params[key] = value
        except Exception as e:
            # 如果所有尝试都失败，保存为字符串
            global_params[key] = value
    # 如果 save_to_file 为 True，则保存到 preferences.json
    if save_to_file:
        save_preference(key, global_params[key])
    print(f"参数 {key} 已设置")

# 修改 set_param_handler 函数以支持 /set 和 /set2 命令
def set_param_handler(command_args, save_to_file=True):
    args = command_args.split()
    if len(args) < 2:
        print("错误：/set 命令需要两个参数，例如 /set context_limit 30")
        return
    if len(args) > 2:
        print("暂时不支持多个参数，将在后续优化")
        return
    key, value = args
    set_param(key, value, save_to_file)

def get_param_handler(command_args):
    if command_args:
        value = get_param(command_args)
        print(f"{command_args}: {value}")
    else:
        params = get_param()
        print("当前参数值：")
        for key, value in params.items():
            print(f"{key}: {value}")

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
        "model": global_params["model"] if "model" in global_params else "deepseek-chat",
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
        global_params["limit_has_reached_dont_show_tip_again"] = False
        global_params["load_from"] = filename
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

def clear_handler(messages):
    messages.clear()
    messages.append({"role": "system", "content": system_prompt})
    global_params["limit_has_reached_dont_show_tip_again"] = False
    print("对话历史已清空。")
    return True

def clear_screen():
    print("\033[2J\033[H", end="", flush=True)

def passwd_handler(command_args):
    global CONFIG_APIKEY
    args = command_args.split()
    
    if not args:
        # 显示当前 API Key
        print(f"当前 API Key (3秒后清除):\n\033[92m{CONFIG_APIKEY}", end="\r", flush=True)
        time.sleep(3)  # 延迟 3 秒
        print("*" * (len(CONFIG_APIKEY) + 30) + "\r")  # 清除显示
        return True
    
    new_api_key = args[0]
    persist = "--persist" in args
    
    # 更新 API Key
    CONFIG_APIKEY = new_api_key
    print(f"\033[92mAPI Key 已更新。\033[0m")
    
    if persist:
        # 保存到文件
        try:
            with open("skapikey.txt", 'w') as file:
                file.write(new_api_key)
            print(f"\033[92mAPI Key 已保存到 skapikey.txt。\033[0m")
        except Exception as e:
            print(f"\033[91m保存 API Key 时出错: {e}\033[0m")
    
    return True

def handle_user_command(command, messages):
    global CONFIG_APIKEY
    # 命令处理函数字典
    command_handlers = {
        "exit": lambda: (print("对话结束。"), False),
        "set": lambda: (set_param_handler(command[len("set "):].strip(), save_to_file=True), True),  # /set 保存到文件
        "set2": lambda: (set_param_handler(command[len("set2 "):].strip(), save_to_file=False), True),  # /set2 不保存到文件
        "get": lambda: (get_param_handler(command[len("get "):].strip()), True),  # 新增 /get 命令
        "save": lambda: (save_conversation(messages, command[len("save "):].strip()), True),
        "clear": lambda: clear_handler(messages),
        "balance": lambda: (check_api_account(CONFIG_APIKEY), True),
        "len": lambda: (print(f'对话总条目: {len(messages)}\n对话轮次数: {(len(messages) - 1) / 2}\n当前上下文长度限制: {global_params["context_limit"]}'), True),
        "load": lambda: (load_conversation_handler(command[len("load "):].strip(), messages), True),
        "cls": lambda: (clear_screen(), True),
        "passwd": lambda: (passwd_handler(command[len("passwd "):].strip()), True),  # 新增 /passwd 命令
    }
    # 命令说明字典
    command_docs = {
        "exit": "退出程序。",
        "save": "保存当前对话历史到文件。用法: /save <文件名>",
        "clear": "清空当前对话历史并重置系统提示。",
        "load": "从文件加载对话历史。用法: /load <文件名>",
        "cls": "清屏。",
        "set": "设置应用程序的相关参数。用法: /set <参数名> <值>",  # 新增 /set 说明
        "set2": "临时设置应用程序的相关参数（不保存到 preferences.json）。用法: /set2 <参数名> <值>",
        "get": "获取应用程序的参数值。用法: /get <参数名> 或 /get",  # 新增 /get 说明
        "len": "获取当前对话的上下文长度。",
        "balance": "查询账户余额。",
        "passwd": "显示或更新 API Key。用法: /passwd [<NewValue>] [--persist]",
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
    global CONFIG_APIKEY
    # 启用虚拟终端模式（仅在 Windows 上生效）
    enable_vt_mode()
    #api_key = 
    read_api_key("skapikey.txt")
    load_preferences()
    if not global_params["skip_account_check"]:
        # 检测 API Key 是否有效并打印账户余额
        if not check_api_account(CONFIG_APIKEY):
            print("\033[91mAPI Key 无效，请检查后重试。\033[0m")
            exit(1)
    else:
        print("\033[92m正在跳过 API Key 检查。\033[0m")

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

        # 检查上下文消息数量是否超过上限
        if global_params["context_limit"] != 0 and ((len(messages) - 1 +1) / 2) > global_params["context_limit"]:
            # 只在第一次达到限制时显示提示
            if "limit_has_reached_dont_show_tip_again" not in global_params or global_params["limit_has_reached_dont_show_tip_again"] == False:
                print("\033[33m提示：上下文消息数量已达到上限，将删除最早的消息。使用 /set context_limit 修改限制，或设为 0 以移除此限制（不推荐）。\033[0m")
                global_params["limit_has_reached_dont_show_tip_again"] = True  # 标记限制已触发
            # 删除最早的用户消息和助手消息
            for i in range(2):
                messages.pop(1)  # 删除索引 1 的消息（用户消息），然后删除新的索引 1 的消息（助手消息）
        
        # 添加用户消息到对话历史
        messages.append({"role": "user", "content": user_message})

        try:
            # 获取助手的回复
            assistant_message = get_assistant_response(CONFIG_APIKEY, messages)
            #print(f"助手: {assistant_message}")

            # 将助手的回复添加到对话历史
            messages.append({"role": "assistant", "content": assistant_message})
        except Exception as e:
            print(f"调用提供程序时发生错误: {e}")
            continue  # 继续对话，而不是退出
    print("正在退出。")


if __name__ == "__main__":
    main()
