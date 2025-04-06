# DeepSeekChat

Demo of DeepSeek-API (Python)

## 介绍

DeepSeekChat 是一个基于 DeepSeek API 的演示项目。本项目使用 Python 语言编写。

## 使用

0. 安装 Python 环境
1. 下载 [pychatv6.py](./pychatv6.py) (最新版)
2. 使用以下命令安装依赖库: `pip install requests` 或 `python -m pip install requests`
3. 如果是第一次使用，需要在当前目录下创建 `skapikey.txt` 填写您的 **DeepSeek** API Key
4. 打开下载的 Python 文件
5. 开始对话

## 全局参数

本项目使用以下默认全局参数，可通过 `/set` 或 `/set2` 命令修改：

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `api_key_filename` | `skapikey.txt` | API Key 存储文件名 |
| `context_limit` | `20` | 上下文消息数量上限 |
| `skip_account_check` | `False` | 启动时跳过 API Key 检查 |
| `model` | `deepseek-chat` | 默认使用的模型 |
| `thinking_tag/begin` | `<think>` | 思维链标记起始符 |
| `thinking_tag/end` | `</think>` | 思维链标记结束符 |
| `cot_in_context` | `False` | 是否将思维链(COT)保留在上下文中 |
| `prompt_preload` | `None` | 预加载的提示词（跳过询问） |
| `render_code_block` | `True` | 是否渲染代码块样式 |
| `prompt_inject` | `True` | 自动注入系统时间等提示词，防止 AI 时间错乱 |
| `language` | `auto` | 界面语言（auto/zh/en等） |
| `temperature` | `1.3` | 模型的 temperature，参考： https://api-docs.deepseek.com/zh-cn/quick_start/parameter_settings |

可通过 `/get [参数名]` 查看当前值。使用 `/set` 永久修改，或使用 `set2` 临时修改。

## Command List

本项目提供了丰富的 `slash command` 支持，具体列表如下:

### 基础命令
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/exit` | 退出程序 | `/exit` |
| `/cls` | 清屏 | `/cls` |
| `/help` | 查看帮助 | `/help` 或 `/help <命令名>` |
| `/about` | (**暂未实现**) 进入交互式关于信息 | `/about` |

### 对话管理
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/save` | 保存当前对话历史 | `/save conversation1.json` |
| `/load` | 加载对话历史 | `/load conversation1.json` |
| `/clear` | 清空当前对话历史 | `/clear` |
| `/len` | 查看对话长度 | `/len` |
| `/input` | 多行输入模式 | `/input` (然后输入内容，按Ctrl+D/Z结束) |
| `/i` | `/input`的别名 | `/i` |

### 附件管理
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/attach` | (**暂未实现**) 添加附件 | `/attach file.txt` |
| `/attachment` | (**暂未实现**) 管理附件 | `/attachment list`<br>`/attachment show 1`<br>`/attachment remove 1` |

### 参数设置
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/set` | 设置参数（持久化） | `/set context_limit 4096` |
| `/set2` | 临时设置参数 | `/set2 temperature 0.7` |
| `/get` | 获取参数值 | `/get context_limit` |

### API 相关
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/passwd` | 管理API Key | `/passwd your_new_key --persist` |
| `/balance` | 查询账户余额 | `/balance` |
| `/topup` | 打开充值页面 | `/topup` |
| `/top-up` | `/topup`的别名 | `/top-up` |
| `/recharge` | `/topup`的别名 | `/recharge` |

### 提示词管理
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/prompt` | 管理提示词 | `/prompt set 你是一个专业助手`<br>`/prompt get`<br>`/prompt reset`<br>`/prompt preload` |

### 系统功能
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/shell` | 执行系统命令 | `/shell ls -l` |

### 其他命令
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/homepage` | 打开项目主页 | `/homepage` |
| `/license` | (**暂未实现**) 查看许可证信息 | `/license` |

可以使用 `/help` 或者 `/help <command>` 查看详细说明。

## LICENSE

**GPL-3.0**
