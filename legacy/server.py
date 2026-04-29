"""
Web API 服务器
=============
提供 HTTP 接口供前端调用

运行：python server.py
访问：http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from openai import OpenAI
import json
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 初始化
app = FastAPI(title="My First Agent API", version="1.0.0")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# 会话存储
sessions = {}

# ========== 数据模型 ==========

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[dict] = []
    session_id: str

class ToolCallLog(BaseModel):
    name: str
    args: dict
    result: str

# ========== API 端点 ==========

@app.get("/")
async def root():
    """返回首页"""
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    聊天接口
    
    - session_id: 会话 ID（用于保持对话历史）
    - message: 用户消息
    
    返回 Agent 回复和工具调用记录
    """
    # 获取或创建会话
    if req.session_id not in sessions:
        sessions[req.session_id] = [
            {"role": "system", "content": "你是一个有用的 AI 助手，可以使用工具来帮助用户。"}
        ]
    
    messages = sessions[req.session_id]
    messages.append({"role": "user", "content": req.message})
    
    tool_calls_log = []
    
    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOL_DEFINITIONS
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                tool_calls_log.append({
                    "name": tool_name,
                    "args": tool_args
                })
                
                # 执行工具
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](**tool_args)
                else:
                    result = f"错误：未知工具 {tool_name}"
                
                # 返回结果给 LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            return ChatResponse(
                reply=message.content,
                tool_calls=tool_calls_log,
                session_id=req.session_id
            )

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"session_id": session_id, "messages": sessions[session_id]}

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清空会话历史"""
    if session_id in sessions:
        sessions[session_id] = [
            {"role": "system", "content": "你是一个有用的 AI 助手，可以使用工具来帮助用户。"}
        ]
    return {"status": "ok", "session_id": session_id}

@app.get("/sessions")
async def list_sessions():
    """列出所有活跃会话"""
    return {"sessions": list(sessions.keys()), "count": len(sessions)}

# ========== 启动服务器 ==========

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀  启动 Agent Web 服务器")
    print("=" * 50)
    print("📍 访问地址：http://localhost:8000")
    print("📍 API 文档：http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
