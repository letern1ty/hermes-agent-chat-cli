"""
Web 聊天服务器（支持模型选择）
============================
提供 HTTP 接口供前端调用，支持切换模型

运行：python web_chat.py
访问：http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from openai import OpenAI
import json
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 初始化 FastAPI
app = FastAPI(title="AI Agent Web Chat", version="1.0.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模型配置
AVAILABLE_MODELS = [
    # 阿里云 Qwen 系列
    {"id": "qwen-plus", "name": "Qwen-Plus（平衡）", "provider": "阿里云", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    {"id": "qwen-max", "name": "Qwen-Max（最强）", "provider": "阿里云", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    {"id": "qwen-turbo", "name": "Qwen-Turbo（最快）", "provider": "阿里云", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    {"id": "qwen3.5-plus", "name": "Qwen3.5-Plus", "provider": "阿里云", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    # DeepSeek 系列
    {"id": "deepseek-chat", "name": "DeepSeek V4 Flash", "provider": "DeepSeek", "base_url": "https://api.deepseek.com"},
    {"id": "deepseek-reasoner", "name": "DeepSeek R1（推理）", "provider": "DeepSeek", "base_url": "https://api.deepseek.com"},
    {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro（高级）", "provider": "DeepSeek", "base_url": "https://api.deepseek.com"},
]

DEFAULT_MODEL = "qwen3.5-plus"

# 初始化客户端（默认用阿里云）
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" if os.getenv("DASHSCOPE_API_KEY") else None

client = OpenAI(api_key=api_key, base_url=base_url)

# 会话存储
sessions = {}

# 数据模型
class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: Optional[str] = DEFAULT_MODEL

class ChatResponse(BaseModel):
    reply: str
    model: str
    session_id: str
    timestamp: str

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str

# 工具定义
TOOLS = {
    "get_weather": lambda city: {
        "北京": "25°C 晴", "上海": "28°C 多云", "深圳": "32°C 小雨",
        "广州": "30°C 阴", "杭州": "26°C 小雨", "纽约": "18°C 阴"
    }.get(city, f"{city}天气数据暂不可用"),
    "calculator": lambda expr: str(eval(expr)) if all(c in "0123456789+-*/.() " for c in expr) else "错误：无效表达式",
    "get_time": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取城市天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式"}},
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "获取当前时间",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# API 端点
@app.get("/")
async def root():
    return FileResponse("web/chat.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/models")
async def list_models():
    return {"models": AVAILABLE_MODELS, "default": DEFAULT_MODEL}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    聊天接口 - 支持多模型切换
    
    流程：
    1. 根据 model 参数查找模型配置
    2. 获取对应的 API Key 和 base_url
    3. 创建临时客户端调用 API
    """
    if req.session_id not in sessions:
        sessions[req.session_id] = [
            {"role": "system", "content": "你是一个有用的 AI 助手。"}
        ]
    
    messages = sessions[req.session_id]
    messages.append({"role": "user", "content": req.message})
    
    # ========== 第 1 步：查找模型配置 ==========
    model_config = None
    for m in AVAILABLE_MODELS:
        if m["id"] == (req.model or DEFAULT_MODEL):
            model_config = m
            break
    
    if not model_config:
        model_config = {"id": DEFAULT_MODEL, "base_url": base_url}
    
    # ========== 第 2 步：获取对应 API Key ==========
    # 根据 provider 选择不同的环境变量
    provider = model_config.get("provider", "阿里云")
    if provider == "DeepSeek":
        model_api_key = os.getenv("DEEPSEEK_API_KEY") or api_key
        model_base_url = model_config.get("base_url", "https://api.deepseek.com")
    else:
        # 阿里云
        model_api_key = api_key
        model_base_url = model_config.get("base_url", base_url)
    
    # ========== 第 3 步：创建临时客户端 ==========
    temp_client = OpenAI(api_key=model_api_key, base_url=model_base_url)
    
    # ========== 第 4 步：调用 LLM ==========
    response = temp_client.chat.completions.create(
        model=model_config["id"],
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto"
    )
    
    message = response.choices[0].message
    messages.append(message)
    
    tool_results = []
    if message.tool_calls:
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            if tool_name in TOOLS:
                result = TOOLS[tool_name](**tool_args)
                tool_results.append({"name": tool_name, "args": tool_args, "result": result})
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        if tool_results:
            response = temp_client.chat.completions.create(
                model=model_config["id"],
                messages=messages
            )
            message = response.choices[0].message
            messages.append(message)
    
    return ChatResponse(
        reply=message.content,
        model=model_config["id"],
        session_id=req.session_id,
        timestamp=datetime.now().isoformat()
    )

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"session_id": session_id, "messages": sessions[session_id]}

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    if session_id in sessions:
        sessions[session_id] = [{"role": "system", "content": "你是一个有用的 AI 助手。"}]
    return {"status": "ok", "session_id": session_id}

@app.get("/sessions")
async def list_sessions():
    return {"sessions": list(sessions.keys()), "count": len(sessions)}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 AI Agent Web Chat 服务器")
    print("=" * 50)
    print(f"📍 访问地址：http://localhost:8000")
    print(f"📍 API 文档：http://localhost:8000/docs")
    print(f"📍 默认模型：{DEFAULT_MODEL}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
