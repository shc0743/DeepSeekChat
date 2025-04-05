#!/bin/bash

# 从 skapikey.txt 文件中读取 API Key
API_KEY=$(cat skapikey.txt)

# 检查 API Key 是否为空
if [ -z "$API_KEY" ]; then
  echo "API Key 未找到或为空，请确保 skapikey.txt 文件中有有效的 API Key。"
  exit 1
fi

# 请求用户输入
echo "请输入您的消息："
read -r USER_MESSAGE

# 对用户输入的内容进行 JSON 转义（仅转义双引号和反斜杠）
ESCAPED_MESSAGE=$(echo "$USER_MESSAGE" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')

# 使用 curl 调用 API
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
        "model": "deepseek-chat",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "'"$ESCAPED_MESSAGE"'"}
        ],
        "stream": false
      }'