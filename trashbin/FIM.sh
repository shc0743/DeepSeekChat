#!/bin/bash

# 定义全局变量
MAX_ATTEMPTS=20           # 最大尝试次数
OUTPUT_FILE="FIM_out.txt"     # 输出文件名
WAIT_TIME=30              # 最小等待时间（秒）
INIT_FILE="FIM_init.txt"  # 初始内容文件

# 定义颜色控制字符
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # 重置颜色

# 检查初始内容文件是否存在
if [ ! -f "$INIT_FILE" ]; then
  echo -e "${RED}错误：$INIT_FILE 文件不存在！${NC}"
  exit 1
fi

# 从初始内容文件中读取内容
INIT_CONTENT=$(cat "$INIT_FILE")

# 初始化尝试次数
attempt=1

# 循环直到 curl 执行时间超过 WAIT_TIME 秒或达到最大尝试次数
while [ $attempt -le $MAX_ATTEMPTS ]; do
  echo -e "${YELLOW}第 $attempt 次尝试...${NC}"

  # 将初始内容写入输出文件
  echo "$INIT_CONTENT" > "$OUTPUT_FILE"

  # 记录开始时间
  START_TIME=$(date +%s)

  # 执行 curl 请求（不限制执行时间）
  curl -L -X POST 'https://api.deepseek.com/beta/completions' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer sk-73f9a7313bad49c195c60db3556035af' \
  --data-raw '{
    "model": "deepseek-chat",
    "prompt": "'"$INIT_CONTENT"'",
    "echo": false,
    "frequency_penalty": 0,
    "logprobs": 0,
    "max_tokens": 8192,
    "presence_penalty": 0,
    "stop": null,
    "stream": false,
    "stream_options": null,
    "suffix": null,
    "temperature": 2,
    "top_p": 1
  }' >> "$OUTPUT_FILE"

  # 记录结束时间并计算执行时间
  END_TIME=$(date +%s)
  ELAPSED_TIME=$((END_TIME - START_TIME))

  # 检查 curl 的执行时间
  if [ $ELAPSED_TIME -ge $WAIT_TIME ]; then
    echo -e "${GREEN}curl 执行时间超过 ${WAIT_TIME} 秒（实际耗时：${ELAPSED_TIME} 秒），脚本退出。${NC}"
    break
  else
    echo -e "${RED}curl 执行时间不足 ${WAIT_TIME} 秒（实际耗时：${ELAPSED_TIME} 秒），正在重新生成...${NC}"
  fi

  # 增加尝试次数
  attempt=$((attempt + 1))
done

# 如果达到最大尝试次数仍未满足条件
if [ $attempt -gt $MAX_ATTEMPTS ]; then
  echo -e "${RED}已达到最大尝试次数 ($MAX_ATTEMPTS 次)，脚本退出。${NC}"
fi
