"""
第 1 天 - 第一个 LLM 调用
=========================
目标：用 Python 调用 Qwen API，看到 AI 回复
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化客户端（使用阿里云 Qwen API）
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 调用 LLM
response = client.chat.completions.create(
    model="qwen-plus",  # 使用 Qwen 模型
    messages=[
        {"role": "system", "content": "你是一个友好的 AI 助手"},
        {"role": "user", "content": "你好，请自我介绍"}
    ]
)

# 打印回复
print("AI 回复：")
print(response.choices[0].message.content)
