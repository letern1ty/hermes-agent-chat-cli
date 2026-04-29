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
import traceback

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

DEFAULT_MODEL = "deepseek-v4-pro"

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
    mode: Optional[str] = "direct"  # "direct" 或 "agent"

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
    "calculator": lambda expression: str(eval(expression)) if all(c in "0123456789+-*/.() " for c in expression) else "错误：无效表达式",
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
    # Agent 模式：带思考步骤和工具调用
    if req.mode == "agent":
        return await agent_chat(req)

    # 直接模式：原始的简单对话
    if req.session_id not in sessions:
        sessions[req.session_id] = [{"role": "system", "content": "你是一个有用的 AI 助手。"}]
    
    messages = sessions[req.session_id]
    messages.append({"role": "user", "content": req.message})
    
    model_config = _get_model_config(req.model)
    model_api_key, model_base_url = _get_provider_config(model_config)
    temp_client = OpenAI(api_key=model_api_key, base_url=model_base_url)
    
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
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        
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


def _get_model_config(model_id):
    for m in AVAILABLE_MODELS:
        if m["id"] == (model_id or DEFAULT_MODEL):
            return m
    return {"id": DEFAULT_MODEL, "base_url": "https://api.deepseek.com", "provider": "DeepSeek"}


def _get_provider_config(model_config):
    provider = model_config.get("provider", "DeepSeek")
    if provider == "DeepSeek":
        key = os.getenv("DEEPSEEK_API_KEY") or api_key
        url = model_config.get("base_url", "https://api.deepseek.com")
    else:
        key = api_key
        url = model_config.get("base_url", base_url)
    return key, url


async def agent_chat(req: ChatRequest) -> ChatResponse:
    """
    Agent 模式聊天 - 带思考步骤展示 + 工具调用
    回复格式：思考步骤 + 最终答案
    """
    model_config = _get_model_config(req.model)
    model_api_key, model_base_url = _get_provider_config(model_config)
    temp_client = OpenAI(api_key=model_api_key, base_url=model_base_url)
    
    # 管理 Agent 会话
    if req.session_id not in sessions:
        sessions[req.session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    messages = sessions[req.session_id]
    messages.append({"role": "user", "content": req.message})
    
    # 构建回复：包含步骤和最终答案
    step_messages = []
    max_rounds = 5
    
    for _ in range(max_rounds):
        response = temp_client.chat.completions.create(
            model=model_config["id"],
            messages=messages,
            tools=AGENT_TOOL_DEFINITIONS,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        # 有工具调用
        if message.tool_calls:
            step_info = {"thought": message.content or "我来分析一下...", "tool_calls": []}
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = TOOLS[tool_name](**tool_args) if tool_name in TOOLS else "未知工具"
                step_info["tool_calls"].append({
                    "name": tool_name,
                    "args": tool_args,
                    "result": tool_result
                })
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_result})
            step_messages.append(step_info)
        else:
            # 最终回答
            final_answer = message.content
            
            # 用带步骤的格式返回
            steps_text = ""
            if step_messages:
                steps_text += "🤔 **思考过程**\n\n"
                for i, step in enumerate(step_messages, 1):
                    if step["thought"]:
                        steps_text += f"{step['thought']}\n\n"
                    for tc in step["tool_calls"]:
                        icon = {"get_weather": "🌤️", "calculator": "🧮", "get_time": "⏰", "search_files": "🔍",
                                "read_file": "📖", "write_file": "✏️", "run_command": "💻"}.get(tc["name"], "🔧")
                        args_str = ", ".join(f"{k}={v}" for k, v in tc["args"].items())
                        steps_text += f"{icon} **{tc['name']}**({args_str})\n"
                        steps_text += f"   → {tc['result']}\n\n"
                steps_text += "---\n\n"
            
            full_reply = steps_text + final_answer
            
            return ChatResponse(
                reply=full_reply,
                model=model_config["id"],
                session_id=req.session_id,
                timestamp=datetime.now().isoformat()
            )
    
    return ChatResponse(
        reply="抱歉，思考步数过多，请重试。",
        model=model_config["id"],
        session_id=req.session_id,
        timestamp=datetime.now().isoformat()
    )


SYSTEM_PROMPT = """你是一个 AI Agent，会像人类一样一步步思考问题。

【能力】你可以使用工具来处理问题，步骤如下：
1. 理解用户需求
2. 思考需要调用什么工具
3. 调用工具获取结果
4. 基于结果给出最终答案

【工具】
- get_weather(city): 查询城市天气
- calculator(expression): 计算数学表达式
- get_time(): 获取当前时间

【回复格式】
每次回复先说出你的思考，然后决定是否调用工具。最终给出完整答案。"""

AGENT_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取城市天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名，如北京、上海"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，支持 + - * /",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式，如 2+2"}},
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


# 老的 /chat 保持兼容
# 下面的辅助函数被新版 /chat 替代

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
