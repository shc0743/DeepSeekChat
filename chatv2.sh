#!/bin/bash

# 从 skapikey.txt 文件中读取 API Key
API_KEY=$(cat skapikey.txt)

# 检查 API Key 是否为空
if [ -z "$API_KEY" ]; then
  echo "API Key 未找到或为空，请确保 skapikey.txt 文件中有有效的 API Key。"
  exit 1
fi

# 初始化对话历史
MESSAGES='[
  {"role": "system", "content": "You are a helpful assistant."}
]'

# 进入连续对话循环
while true; do
  # 请求用户输入
  echo -n "你: "
  read -r USER_MESSAGE

  # 如果用户输入 "exit"，退出脚本
  if [[ "$USER_MESSAGE" == "exit" ]]; then
    echo "对话结束。"
    break
  fi

  # 对用户输入的内容进行 JSON 转义（仅转义双引号和反斜杠）
  ESCAPED_MESSAGE=$(echo "$USER_MESSAGE" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')

  # 将用户输入添加到对话历史中
  MESSAGES=$(echo "$MESSAGES" | sed '$s/\]$//') # 移除末尾的 ]
  MESSAGES+=",{\"role\": \"user\", \"content\": \"$ESCAPED_MESSAGE\"}]"

  # 使用 curl 调用 API
  RESPONSE=$(curl -s https://api.deepseek.com/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d '{
          "model": "deepseek-chat",
          "messages": '"$MESSAGES"',
          "stream": false
        }')

  # 提取助手的回复（使用 grep 和 sed 代替 jq）
  ASSISTANT_MESSAGE=$(echo "$RESPONSE" | grep -oP '"content":"\K[^"]*')

  # 将助手的回复添加到对话历史中
  MESSAGES=$(echo "$MESSAGES" | sed '$s/\]$//') # 移除末尾的 ]
  MESSAGES+=",{\"role\": \"assistant\", \"content\": \"$ASSISTANT_MESSAGE\"}]"

  # 打印助手的回复
  echo "助手: $ASSISTANT_MESSAGE"
done