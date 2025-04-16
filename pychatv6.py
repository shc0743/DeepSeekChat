import json
import os
import ctypes
import requests
import platform
import time
import sys
import webbrowser
from ctypes import wintypes
import locale
from datetime import datetime, timezone
import copy
import readline # fix the input bug

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

# 打开充值页面
def open_top_up_page():
    top_up_url = "https://platform.deepseek.com/top_up"
    webbrowser.open(top_up_url)

# 检测 API Key 是否有效，并打印账户余额
def check_api_account(api_key):
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    while True:
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
                user_input = input("是否希望前往充值？(y/N): ").strip().lower()
                if user_input != 'y':
                    return False
                
                # 打开充值页面
                open_top_up_page()
                
                # 询问用户是否完成充值
                user_input = input("是否完成充值？(y/N): ").strip().lower()
                if user_input != 'y':
                    return False
                
                # 继续循环，重新检查余额
                continue

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
    "api_key_filename": "skapikey.txt", # 指定 api key 的存储位置（与配置文件独立）
    "context_limit": 20,  # 默认上下文消息数量上限
    "skip_account_check": False, # 启动时不进行APIKEY检查
    "model": "deepseek-chat",  # 默认模型
    "thinking_tag/begin": "<think>", # 用于 R1
    "thinking_tag/end": "</think>", # 用于 R1
    "cot_in_context": False, # 是否将 COT 作为上下文的一部分
    "prompt_preload": None, # 若指定，则直接使用此提示词，不进行二次询问
    "render_code_block": True, # 是否渲染代码块
    "prompt_inject": True, # 预注入提示词，例如系统时间，防止 AI 出现时间错乱
    "language": "auto", # 语言，用于提示词
    "temperature": 1.3, # 根据建议，“通用对话”建议设为1.3 https://api-docs.deepseek.com/zh-cn/quick_start/parameter_settings
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
        try:
            with open("preferences.json", 'r') as file:
                preferences = json.load(file)
        except FileNotFoundError:
            preferences = {}

        # 新增逻辑：当 value 为 None 时删除键
        if value is None:
            if key in preferences:
                del preferences[key]
        else:
            preferences[key] = value  # 原有逻辑

        with open("preferences.json", 'w') as file:
            json.dump(preferences, file, indent=4)
            print(f"\033[92m√ 已保存 \033[35m", end='')
    except Exception as e:
        print(f"\033[91m! 无法保存 \033[35m", end='')

# 修改 set_param 函数以支持保存单个参数到 preferences.json
def set_param(key, value, save_to_file=True):
    #print('          ', end='')
    try:
        # 如果为 None, 清除此参数
        if value is None:
            if key in global_params:
                del global_params[key]
            # 立即触发保存操作，并传递 value=None 表示删除
            if save_to_file:
                save_preference(key, None)  # 新增此行p
                print(f"参数 {key} 已清除")
            return  # 直接返回
        # 首先尝试解析
        global_params[key] = float(value)
        # 检查是否是整数（如 2.0）
        if global_params[key].is_integer():
            global_params[key] = int(global_params[key])
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
    if len(args) < 1:
        print("错误：/set 命令需要至少1个参数，例如 /set context_limit 30")
        return
    elif len(args) < 2:
        return set_param(command_args, None, save_to_file)
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

# 获取提示词注入内容
def get_inject_prompt():
    # 获取首选语言
    preferred_language = get_param("language")
    # 获取当前时间和时区
    current_time = datetime.now(datetime.now().astimezone().tzinfo).strftime("%Y%m%dT%H%M%S.%f%z")
    tz = datetime.now(datetime.now().astimezone().tzinfo).strftime("%z")
    return f'<system>' + \
        f'PreferredLanguage: {preferred_language}\n' + \
        f'CurrentTime: {current_time}\n' + \
        f'TimeZone: {tz}\n' + \
        f'Notice: These information are for reference only. Don\'t proactively show them unless user asks.' + \
        f'</system>\n\n'
        # TODO f'Memory: 嵌套value\n' + \

# 调用 API 获取助手的回复
def get_assistant_response(api_key, messages):
    messages = copy.deepcopy(messages)  # 使用深拷贝代替浅拷贝 # 复制一份，防止注入提示词时改动原内容
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if get_param("prompt_inject") == True:
        messages[0]['content'] = get_inject_prompt() + messages[0]['content']   
    tem = global_params.get('temperature', 1)
    if not isinstance(tem, (int, float)) or not 0 <= tem <= 2:
        raise ValueError("参数异常，请检查全局配置项 temperature must be a number between 0 and 2")
    data = {
        "model": global_params["model"] if "model" in global_params else "deepseek-chat",
        "messages": messages,
        "stream": True,
        "temperature": tem
    }
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=90)
        # 手动检查状态码而不是使用raise_for_status()
        if response.status_code >= 400:
            # 尝试获取错误详情
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = f"\n错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}"
            except ValueError:
                error_detail = f"\n响应内容: {response.text}"
            
            error_msg = (f"API请求失败，状态码: {response.status_code}\n"
                        f"原因: {response.reason}{error_detail}")
            print(f"API调用异常: {error_msg}")
            return f"API调用异常: {error_msg}"

        assistant_message = ""
        reasoning_buffer = ""  # 用于暂存推理内容
        last_was_reasoning = False  # 跟踪上次内容类型
        last_was_code_block = False  # 跟踪上次内容类型
        
        print("助手: ", end="", flush=True)
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line == "data: [DONE]":
                        # 最终换行处理
                        if last_was_reasoning:
                            print("\033[0m")  # 结束暗淡颜色
                        print("")
                        break
                        
                    if decoded_line.startswith("data:"):
                        try:
                            event_data = json.loads(decoded_line[5:])
                            if "choices" in event_data and event_data["choices"]:
                                delta = event_data["choices"][0].get("delta", {})
                                
                                # 获取内容并分类
                                content = delta.get("content", "")
                                reasoning = delta.get("reasoning_content", "")
                                
                                # 处理推理内容（暗淡灰色）
                                if reasoning:
                                    if not last_was_reasoning:  # 新推理块开始
                                        print(f"\033[90m{global_params.get('thinking_tag/begin', '<｜begin▁of▁thinking｜>')}\n", end="")  # 换行+暗淡颜色
                                    print(reasoning, end="", flush=True)
                                    reasoning_buffer += reasoning
                                    last_was_reasoning = True
                                
                                # 处理正式回答（正常颜色）
                                if content:
                                    if last_was_reasoning:  # 从推理切换到正式回答
                                        print(f"\n{global_params.get('thinking_tag/end', '<｜end▁of▁thinking｜>')}\033[0m\n", end="")  # 结束颜色并换行
                                        last_was_reasoning = False
                                    if global_params.get('render_code_block', False) and content == '```' or content.strip() == '```': # 对于 AI 模型，“```”通常会在同一个token
                                        if last_was_code_block:
                                            print(f"{content}\033[0m", end="", flush=True)
                                            last_was_code_block = False
                                        else:
                                            print(f"\033[96m{content}", end="", flush=True)
                                            last_was_code_block = True
                                    else:
                                        print(content, end="", flush=True)
                                    assistant_message += content  # 只存储正式内容
                                    
                        except json.JSONDecodeError as e:
                            print(f"\n解析 JSON 时出错: {e}")
                            continue

        except KeyboardInterrupt:
            print("\n\n\033[91m用户中断\033[0m")
            
        if get_param('cot_in_context') is True:
            return (f"<｜begin▁of▁thinking｜>{reasoning_buffer}<｜end▁of▁thinking｜>{assistant_message}")
        return assistant_message
        
    except requests.exceptions.RequestException as e:
        error_msg = f"请求异常: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_text = e.response.text
                if error_text:
                    error_msg += f"\n响应内容: {error_text}"
            except:
                pass
        print(f"API调用异常: {error_msg}")
        return f"API调用异常: {error_msg}"

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
            with open(get_param("api_key_filename"), 'w') as file:
                file.write(new_api_key)
            print(f"\033[92mAPI Key 已保存到 skapikey.txt。\033[0m")
        except Exception as e:
            print(f"\033[91m保存 API Key 时出错: {e}\033[0m")
    
    return True

def prompt_handler(command_args, messages):
    args = command_args.split()
    global system_prompt
    if len(args) < 1:
        print("错误：使用 /help prompt 命令获取帮助。")
        return
    action = args[0]
    if action == "get":
        print(f"当前提示词: {system_prompt}")
    elif action == "set":
        # 直接解析原始字符串，以避免空格问题
        new_prompt = command_args[len(action) + 1:].strip()
        if not new_prompt:
            print("错误：如果要清空提示词，请使用 /prompt reset 。")
            return
        system_prompt = new_prompt
        # 更新系统提示
        messages[0]["content"] = system_prompt
        print(f"\033[92m提示词已更新。")
    elif action == "reset":
        # 重置提示词
        system_prompt = ''
        messages[0]["content"] = system_prompt
        print("\033[92m提示词已重置。")
    elif action == "preload":
        # 预加载提示词
        new_prompt = command_args[len(action) + 1:].strip()
        if not new_prompt:
            new_prompt = system_prompt
        set_param("prompt_preload", system_prompt)
        # print(f"\033[92m提示词已预加载。")
    elif action == "reset-preload":
        # 重置预加载提示词
        set_param("prompt_preload", None)
    else:
        print("错误：未知操作。使用 /help prompt 命令获取帮助。")
        return
    return True
        
def shell_command_handler(command_args):
    if not command_args:
        if platform.system() == "Windows":
            command_args = "cmd.exe"
        else:
            command_args = "bash"

    try:
        print('\033[0m', end='', flush=True)
        code = os.system(command_args)
        print('\n', end='')
        print(f'\033[92m命令执行成功\033[94m 返回: \033[96m{code}\033[0m')
    except BaseException as e:
        print(f"执行命令时出错: {e}")
        return False

    return True

def interactive_input_handler(command_args):
    EOF = 'EOF'
    if command_args:
        EOF = command_args
    message = []
    while True:
        try:
            user_input = input(f"\033[96m# \033[94m") # 按原样存储
            if user_input == EOF:
                break
            message.append(user_input)
        except EOFError: 
            break
        except KeyboardInterrupt:
            print("\n\033[91m取消此次输入请求。\033[0m")
            return True
    message = '\n'.join(message)
    if not message or message.isspace():
        print("\033[31m没有输入内容。\033[0m")
        return True
    return {"modify_user_message": True, "data": (message)}

def homepage_handler():
    homepages = [
        'https://redirect-static.chcs1013.com/redirect?id=pychatapp',
        'https://github.com/shc0743/DeepSeekChat/',
    ]
    # 使用 request 测试各个主页的连通性 （多线程）
    print('Testing network connectivity...')
    import concurrent.futures

    def test_homepage_connectivity(url):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return url, True
            return url, False
        except requests.RequestException:
            return url, False

    def homepage_handler2(homepages):
        accessible_homepages = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(test_homepage_connectivity, homepages)

        for url, is_accessible in results:
            if is_accessible:
                accessible_homepages.append(url)
        return accessible_homepages
    
    accessible_homepages = homepage_handler2(homepages)
    if not accessible_homepages:
        for url in homepages:
            print(f"\033[91m!\033[0m   {url}\033[0m")
        print("\033[31m所有主页均无法访问。\033[0m")
        return
    for url in homepages:
        ok = url in accessible_homepages
        print(f"{'\033[92m*' if ok else '\033[91m!'}\033[0m {'* ' if url == accessible_homepages[0] else '  '}{url}\033[0m")
    
    print(f'Attempting to open: {accessible_homepages[0]}')
    webbrowser.open(accessible_homepages[0])

def handle_user_command(command, messages):
    global CONFIG_APIKEY
    # 命令处理函数字典
    command_handlers = {
        "exit": lambda: (print("对话结束。"), False),
        "set": lambda: (set_param_handler(command[len("set "):].strip(), save_to_file=True), True),
        "set2": lambda: (set_param_handler(command[len("set2 "):].strip(), save_to_file=False), True),
        "get": lambda: (get_param_handler(command[len("get "):].strip()), True),
        "save": lambda: (save_conversation(messages, command[len("save "):].strip()), True),
        "clear": lambda: clear_handler(messages),
        "balance": lambda: (check_api_account(CONFIG_APIKEY), True),
        "len": lambda: (print(f'对话总条目: {len(messages)}\n对话轮次数: {(len(messages) - 1) / 2}\n当前上下文长度限制: {global_params["context_limit"]}'), True),
        "load": lambda: (load_conversation_handler(command[len("load "):].strip(), messages), True),
        "cls": lambda: (clear_screen(), True),
        "passwd": lambda: (passwd_handler(command[len("passwd "):].strip()), True),
        "topup": lambda: (open_top_up_page(), True),
        "top-up": lambda: (open_top_up_page(), True),
        "recharge": lambda: (open_top_up_page(), True),
        "prompt": lambda: (prompt_handler(command[len("prompt "):].strip(), messages), True),
        "shell": lambda: (shell_command_handler(command[len("shell "):].strip()), True),
        "input": lambda: (interactive_input_handler(command[len("input "):].strip())),
        "i": lambda: (interactive_input_handler(command[len("i "):].strip())),
        "homepage": lambda: (homepage_handler(), True),
        "debug:get_inject_prompt": lambda: (print(get_inject_prompt()), True),
    }
    # 命令说明字典
    command_docs = {
        "exit": "退出程序。",
        "save": "保存当前对话历史到文件。用法: /save <文件名>",
        "load": "从文件加载对话历史。用法: /load <文件名>",
        "clear": "清空当前对话历史但不重置系统提示。如果要重置系统提示，请使用 /prompt reset。",
        "cls": "清屏。",
        "input": "允许用户打开交互式输入 Shell 以输入多行文本。",
        "i": "input 的别名。",
        "attach": "将附件添加到对话上下文。用法: /attach <文件名>",
        "attachment": "管理当前对话的附件。用法: /attachment <list|show|remove> [<附件 ID>]",
        "set": "设置或清除应用程序的相关参数。",
        "set2": "临时设置应用程序的相关参数（不保存到 preferences.json）。",
        "get": "获取应用程序的参数值。用法: /get <参数名> 或 /get",
        "len": "获取当前对话的上下文长度。",
        "prompt": "管理提示词。用法: /prompt <get|set|reset|preload|reset-preload> [<提示词>]",
        "passwd": "显示或更新 API Key。用法: /passwd [<NewValue>] [--persist]",
        "shell": "打开系统 Shell。用法: /shell [command]",
        "balance": "查询账户余额。",
        "topup": "打开充值页面。", "top-up": "打开充值页面。", "recharge": "打开充值页面。",
        "help": "显示所有可用命令及其说明。使用 /help [<command>] 查看子命令的具体用法。",
        "about": "进入交互式 关于信息 Shell。",
        "license": "\033[94m[本项目使用 \033[96mGPL-3.0\033[94m]\033[0m 显示许可证信息。",
        "homepage": "打开项目主页。",
        "debug:get_inject_prompt": "Call get_inject_prompt()",
    }
    # 命令说明字典
    command_details = {
        "save": "/save <文件名>",
        "load": "/load <文件名>",
        "input": f"打开交互式输入 Shell 以输入多行文本。\n\t\t/input\n\t\t/input [<EOF>]\n/input\t\t打开交互式输入 Shell 以输入多行文本。默认使用 EOF 作为消息结束的标志。\n/input <EOF>\t打开交互式输入 Shell 以输入多行文本，使用提供的 <EOF> 作为消息结束的标志。\n对于每一个子命令，也可以通过按下 Ctrl+{ 'Z' if platform.system() == 'Windows' else 'D' } 来结束输入。或者，使用 Ctrl+C 取消输入。",
        "i": "打开交互式输入 Shell 以输入多行文本。这是 input 的别名。使用 /help input 查看帮助。",
        "attach": "将附件添加到对话上下文。\n用法: /attach <文件名>\n注意：暂时无法修改附件的附加细节。",
        "attachment": "管理当前对话的附件。\n用法: /attachment <list|show|remove> [<附件 ID>]\nlist\t列出所有附件。\nshow\t显示指定附件的内容。\nremove\t移除指定的附件。",
        "set": "设置或清除参数。\n用法: /set <参数名> [<值>]",
        "set2": "临时设置应用程序的相关参数（不保存到 preferences.json）。\n用法: /set2 <参数名> <值>",
        "get": "/get\n\t/get <参数名>",
        "passwd": "显示或更新 API Key。\n用法:\n\t/passwd [<NewValue>] [--persist]\n--persist    将 API Key 保存到文件。",
        "prompt": "提示词管理。\n用法:\n\t/prompt get\n\t/prompt set <提示词>\n\t/prompt reset\n\t/prompt preload [<提示词>]\n\t/prompt reset-preload\nget\t获取当前提示词。\nset <提示词>\t设置新的提示词。\nreset\t清空提示词。\npreload [提示词]\t将提示词写入预定义配置文件。如果没有指定提示词，则写入当前提示词。\nreset-preload\t清空预定义提示词。",
        "shell": "打开系统 Shell。\n用法: /shell [command]\n如果没有指定命令，则打开系统默认 Shell。对于 Windows，默认 Shell 是 cmd.exe；对于 Linux 和 macOS，默认 Shell 是 bash。",
        "balance": "查询账户余额。\n用法: /balance",
        "help": "/help [<command>]",
        "license": "\033[94m[本项目使用 \033[96mGPL-3.0\033[94m]\033[0m 显示许可证信息。\n用法: /license",
    }
    # 单独处理 /help 命令
    command_name = command.split()[0] if command else ""
    if command_name == "help":
        sub_command = command.split()
        if len(sub_command) > 1:
            sub_command = sub_command[1]
            if not sub_command in command_details:
                if sub_command in command_docs:
                    print(f'\033[95m{sub_command}\033[35m 用法:\n\t\033[0m/{sub_command}\033[0m')
                else:
                    print(f'\033[35m{sub_command} 不存在\033[0m')
            else:
                print(f'\033[95m{sub_command}\033[35m 用法:')
                print(f'\033[0m\t{command_details.get(sub_command)}\033[0m')
        else:
            print("\033[35m=== 可用命令 ===\033[0m")
            for cmd, doc in command_docs.items():
                print(f"/{cmd}: {doc}")
            print("\033[35m================\033[0m")
        return True

    # 提取命令名称
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
    "1": "",
    "2": "You are a software developer.",
    "3": "You are a helpful assistant. The user is a Chinese user, so reply in Chinese, unless the user obviously asks you to reply in other languages."
}

def main():
    global system_prompt  # 将 system_prompt 声明为全局变量，以便在 handle_user_command 中使用
    global CONFIG_APIKEY
    # 启用虚拟终端模式（仅在 Windows 上生效）
    enable_vt_mode()
    load_preferences()
    #api_key = 
    read_api_key(get_param("api_key_filename"))
    if not global_params["skip_account_check"]:
        # 检测 API Key 是否有效并打印账户余额
        if not check_api_account(CONFIG_APIKEY):
            print("\033[91mAPI Key 无效，请检查后重试。\033[0m")
            exit(1)
    else:
        print("\033[92m正在跳过 API Key 检查。\033[0m")

    system_prompt = None
    if get_param("prompt_preload") is not None:
        system_prompt = get_param("prompt_preload")
    else:
        # 显示提示词选项
        print("请选择系统提示词（输入编号或手动输入自定义提示词，对于DeepSeek-R1不建议设置提示词）：")
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

    nUserCancelCount = 0
    while True:
        try:
            try:
                user_message = input("\033[36m你: ").strip()
                print("\033[0m", end='')
                
                if not user_message.strip():
                    print("\033[91m输入内容为空。\033[0m")
                    continue
            except BaseException:
                print("\n\033[91m操作被中断\033[0m")
                if nUserCancelCount > 1: # 3次
                    try:
                        input('\033[91m想要退出? 再次按下 Ctrl-C \033[96m')
                    except BaseException:
                        print('\033[0m')
                        break
                nUserCancelCount += 1
                continue
        except BaseException:
            print('\033[91m操作反复被中断\033[0m')

        nUserCancelCount = 0
        # 处理斜杠命令
        if user_message.startswith('/'):
            handle_result = handle_user_command(user_message[1:], messages)
            if not handle_result:  # 去掉斜杠并处理命令
                break
            if isinstance(handle_result, dict) and "modify_user_message" in handle_result and handle_result["modify_user_message"]:
                user_message = handle_result.get("data", user_message)
            else:
                continue  # 跳过后续逻辑，继续等待用户输入

        # 检查上下文消息数量是否超过上限
        # 确保 context_limit 存在，如果不存在则设为默认值 0
        if "context_limit" not in global_params:
            global_params["context_limit"] = 0
        while global_params["context_limit"] != 0 and ((len(messages) - 1 +1) / 2) > global_params["context_limit"]:
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
            messages.append({"role": "assistant", "content": 'Unexpected ' + str(e)})
            continue  # 继续对话，而不是退出
    print("正在退出。")


if __name__ == "__main__":
    main()
