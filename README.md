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

## Command List

本项目提供了丰富的 `slash command` 支持，具体列表如下:

### 基础命令
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/exit` | 退出程序 | `/exit` |
| `/cls` | 清屏 | `/cls` |
| `/help` | 查看帮助 | `/help` 或 `/help <命令名>` |

### 对话管理
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/save` | 保存当前对话历史 | `/save conversation1.json` |
| `/load` | 加载对话历史 | `/load conversation1.json` |
| `/clear` | 清空当前对话历史 | `/clear` |
| `/len` | 查看对话长度 | `/len` |

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

### 高级功能
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/prompt` | 管理提示词 | `/prompt set "你是一个专业助手"` |
| `/input` | 多行输入模式 | `/input` (然后输入内容，按Ctrl+D（或Z）结束) |
| `/shell` | 执行系统命令 | `/shell ls -l` |
| `/attach` | 添加附件 | `/attach file.txt` |

### 其他命令
| 命令 | 说明 | 用法示例 |
|------|------|----------|
| `/homepage` | 打开项目主页 | `/homepage` |
| `/license` | 查看许可证信息 | `/license` |

## LICENSE

**GPL-3.0**
