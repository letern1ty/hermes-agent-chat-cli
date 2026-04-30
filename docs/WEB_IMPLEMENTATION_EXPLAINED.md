# 网页聊天实现详解（逐行注释版）

> 从零理解 Web 聊天应用的完整实现

---

## 📚 整体架构

```
┌─────────────┐         HTTP          ┌─────────────┐
│   浏览器     │ ←──────────────────→  │   Python    │
│  (前端 HTML) │      JSON 数据        │  (后端 API) │
└─────────────┘                       └─────────────┘
       │                                      │
       │ 1. 用户输入消息                       │
       │ 2. 发送 POST /chat                   │
       │                                      │ 3. 调用 LLM API
       │                                      │ 4. 获取回复
       │ 5. 显示 Markdown 渲染的结果           │
```

**技术栈**：
- **前端**: HTML + CSS + JavaScript（无框架，原生）
- **后端**: Python + FastAPI
- **Markdown**: marked.js（前端渲染）
- **代码高亮**: highlight.js

---

## 第一部分：后端代码详解（web_chat.py）

### 第 1 步：导入依赖

```python
# web_chat.py

# FastAPI 框架核心
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# 数据验证（自动验证请求数据格式）
from pydantic import BaseModel
from typing import List, Optional

# 系统和工具库
import os
import json
from datetime import datetime

# 阿里云 DashScope API 客户端（兼容 OpenAI 格式）
from openai import OpenAI

# 环境变量加载（从 .env 文件读取 API Key）
from dotenv import load_dotenv
```

**为什么要导入这些？**
- `FastAPI`: Python 最流行的 Web 框架，性能好，自动文档
- `BaseModel`: 定义数据结构，自动验证
- `OpenAI`: 阿里云 DashScope 兼容 OpenAI 格式，所以用这个库
- `load_dotenv`: 从 `.env` 文件读取敏感信息（API Key）

---

### 第 2 步：加载环境变量

```python
# 从 .env 文件加载环境变量
load_dotenv()

# 获取 API Key（支持两种环境变量名）
# os.getenv() 从系统环境变量读取，如果不存在返回 None
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")

# 根据是否有 DASHSCOPE_API_KEY 决定使用哪个 base_url
# 三元表达式：如果 A 则 B，否则 C
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" if os.getenv("DASHSCOPE_API_KEY") else None

# 初始化 API 客户端
# api_key: 认证密钥（类似密码）
# base_url: API 服务器地址（不传则默认用 OpenAI 官方）
client = OpenAI(api_key=api_key, base_url=base_url)
```

**关键点**：
- `.env` 文件格式：`DASHSCOPE_API_KEY=sk-xxxxx`
- 为什么用 `or`？兼容不同配置习惯
- 为什么需要 `base_url`？阿里云 API 地址和 OpenAI 不同

---

### 第 3 步：定义数据模型

```python
# Pydantic 模型：定义 API 请求的数据结构
# 作用：自动验证、自动文档、类型提示
class ChatRequest(BaseModel):
    """聊天请求的数据结构"""
    
    # session_id: 会话 ID，用于区分不同用户的对话
    # str: 字符串类型
    session_id: str
    
    # message: 用户发送的消息内容
    message: str
    
    # model: 使用的模型名称，Optional 表示可以不传
    # 默认值是 "qwen3.5-plus"
    model: Optional[str] = "qwen3.5-plus"


class ChatResponse(BaseModel):
    """聊天响应的数据结构"""
    
    # reply: AI 的回复内容
    reply: str
    
    # model: 实际使用的模型
    model: str
    
    # session_id: 会话 ID（返回给前端，用于确认）
    session_id: str
    
    # timestamp: 时间戳，ISO 格式（如 "2026-04-29T11:30:00"）
    timestamp: str
```

**为什么定义模型？**
1. **自动验证**: 如果前端传的数据不对，自动返回错误
2. **自动文档**: `/docs` 页面自动生成 API 文档
3. **类型安全**: IDE 可以自动补全、检查错误

---

### 第 4 步：定义工具

```python
# 工具字典：名字 → 函数
# 这些是 AI 可以调用的"能力"
TOOLS = {
    # 天气查询工具
    # lambda: 匿名函数，等价于 def get_weather(city): ...
    "get_weather": lambda city: {
        "北京": "25°C 晴", 
        "上海": "28°C 多云", 
        "深圳": "32°C 小雨",
        "广州": "30°C 阴", 
        "杭州": "26°C 小雨", 
        "纽约": "18°C 阴"
    }.get(city, f"{city}天气数据暂不可用"),
    
    # 计算器工具
    # all(): 检查所有字符是否都在允许集合中
    "calculator": lambda expr: str(eval(expr)) if all(c in "0123456789+-*/.() " for c in expr) else "错误：无效表达式",
    
    # 时间查询工具
    # datetime.now(): 获取当前时间
    # strftime(): 格式化时间字符串
    "get_time": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
```

**工具调用流程**：
```
1. LLM 决定调用工具 → 返回工具名和参数
2. 后端查找 TOOLS 字典 → 执行对应函数
3. 把结果返回给 LLM → LLM 生成最终回复
```

---

### 第 5 步：定义工具描述（给 LLM 看的）

```python
# 工具定义：告诉 LLM 有哪些工具可用，以及怎么用
# 这是 JSON Schema 格式，LLM 靠这个理解工具
TOOL_DEFINITIONS = [
    {
        "type": "function",  # 工具类型：函数
        "function": {
            "name": "get_weather",  # 工具名称（必须和 TOOLS 字典的 key 一致）
            "description": "获取城市天气",  # 工具描述（LLM 根据这个决定什么时候用）
            "parameters": {  # 参数定义
                "type": "object",  # 参数类型：对象
                "properties": {  # 具体参数
                    "city": {
                        "type": "string",  # 参数类型：字符串
                        "description": "城市名"  # 参数描述
                    }
                },
                "required": ["city"]  # 必填参数列表
            }
        }
    },
    # ... 其他工具类似
]
```

**为什么需要这个？**
- LLM 不知道你的代码有什么函数
- 通过这个描述，LLM 知道"哦，有个天气工具，需要 city 参数"
- 格式是 OpenAI 的标准，所有兼容 API 都用这个

---

### 第 6 步：初始化 FastAPI 应用

```python
# 创建 FastAPI 应用实例
# title: API 文档标题（访问 /docs 可以看到）
# version: API 版本号
app = FastAPI(title="AI Agent Web Chat", version="1.0.0")

# 添加跨域中间件（CORS）
# 为什么需要？前端和后端如果端口不同，浏览器会拦截请求
# 这个配置允许任何来源访问（开发环境方便，生产环境要限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST 等）
    allow_headers=["*"],  # 允许所有 HTTP 头
)

# 会话存储：用字典存储每个用户的对话历史
# key: session_id, value: 消息列表
sessions = {}
```

**会话为什么用字典？**
- 简单，适合单机
- 生产环境应该用 Redis 等数据库
- 重启后数据会丢失（开发够用）

---

### 第 7 步：定义 API 端点（路由）

```python
# @app.get("/") 是装饰器（Decorator）
# 作用：告诉 FastAPI，当用户访问 GET / 时，执行 root() 函数
@app.get("/")
async def root():
    """
    返回首页
    async: 异步函数，可以同时处理多个请求
    """
    # FileResponse: 返回文件内容（这里是 HTML 文件）
    # "web/chat.html": 文件路径（相对于当前目录）
    return FileResponse("web/chat.html")


# 健康检查端点（用于监控服务是否正常）
@app.get("/health")
async def health_check():
    """健康检查"""
    # 返回 JSON 数据（FastAPI 自动转换字典为 JSON）
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()  # ISO 格式时间
    }


# 获取可用模型列表
@app.get("/models")
async def list_models():
    """获取可用模型列表"""
    return {
        "models": AVAILABLE_MODELS,
        "default": DEFAULT_MODEL
    }
```

**装饰器是什么？**
```python
# 等价于：
def root():
    ...
app.get("/")(root)  # 把函数注册到路由
```

---

### 第 8 步：核心聊天接口

```python
# POST /chat: 接收聊天请求
# response_model=ChatResponse: 指定返回数据结构（自动验证）
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    聊天接口
    
    参数:
        req: ChatRequest 对象（自动解析 JSON 请求体）
        - req.session_id: 会话 ID
        - req.message: 用户消息
        - req.model: 使用的模型
    """
    
    # ========== 第 1 步：获取或创建会话 ==========
    # 如果 session_id 不在 sessions 字典中，创建新会话
    if req.session_id not in sessions:
        sessions[req.session_id] = [
            # 系统消息：设定 AI 的角色和行为
            {"role": "system", "content": "你是一个有用的 AI 助手。"}
        ]
    
    # 获取这个会话的消息历史
    messages = sessions[req.session_id]
    
    # 添加用户消息到历史
    # role: "user" 表示用户消息
    messages.append({"role": "user", "content": req.message})
    
    
    # ========== 第 2 步：调用 LLM ==========
    # client.chat.completions.create(): 调用 API
    response = client.chat.completions.create(
        model=req.model or DEFAULT_MODEL,  # 模型名称
        messages=messages,  # 对话历史
        tools=TOOL_DEFINITIONS,  # 工具定义
        tool_choice="auto"  # 让 LLM 自动决定是否调用工具
    )
    
    # 获取 LLM 返回的第一条消息
    # response.choices: 可能有多个候选回复
    # [0]: 取第一个（最好的）
    # .message: 消息对象
    message = response.choices[0].message
    
    # 把 AI 的消息也加入历史
    messages.append(message)
    
    
    # ========== 第 3 步：处理工具调用 ==========
    tool_results = []  # 记录工具调用结果（用于返回给前端）
    
    # message.tool_calls: LLM 决定调用的工具列表
    if message.tool_calls:
        # 遍历每个工具调用
        for tool_call in message.tool_calls:
            # 获取工具名称和参数
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)  # 参数字符串 → 字典
            
            # 在 TOOLS 字典中查找并执行工具
            if tool_name in TOOLS:
                # **tool_args: 字典解包，等价于 tool(city="北京")
                result = TOOLS[tool_name](**tool_args)
                
                # 记录日志
                tool_results.append({
                    "name": tool_name,
                    "args": tool_args,
                    "result": result
                })
                
                # 把工具结果返回给 LLM
                # role: "tool" 表示工具返回的结果
                # tool_call_id: 关联到具体的工具调用
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        # 如果有工具调用，需要再次调用 LLM
        # 因为 LLM 看到工具结果后才能生成最终回复
        if tool_results:
            response = client.chat.completions.create(
                model=req.model or DEFAULT_MODEL,
                messages=messages  # 包含工具结果的历史
            )
            message = response.choices[0].message
            messages.append(message)
    
    
    # ========== 第 4 步：返回响应 ==========
    return ChatResponse(
        reply=message.content,  # AI 的回复内容
        model=req.model or DEFAULT_MODEL,  # 使用的模型
        session_id=req.session_id,  # 会话 ID
        timestamp=datetime.now().isoformat()  # 时间戳
    )
```

**关键流程图解**：
```
用户消息 → 加入历史 → 调用 LLM → LLM 决定调用工具？
                                    │
                                    ├─ 否 → 返回回复
                                    │
                                    └─ 是 → 执行工具 → 结果给 LLM → 再次调用 → 返回回复
```

---

### 第 9 步：会话管理接口

```python
# 获取会话历史
# {session_id} 是路径参数，如 /history/session_123
@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    # 会话不存在，返回 404 错误
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 返回会话数据
    return {
        "session_id": session_id,
        "messages": sessions[session_id]  # 完整消息历史
    }


# 清空会话历史
@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清空会话历史"""
    if session_id in sessions:
        # 重置为只有系统消息
        sessions[session_id] = [
            {"role": "system", "content": "你是一个有用的 AI 助手。"}
        ]
    return {"status": "ok", "session_id": session_id}


# 列出所有活跃会话
@app.get("/sessions")
async def list_sessions():
    """列出所有活跃会话"""
    return {
        "sessions": list(sessions.keys()),  # 所有 session_id
        "count": len(sessions)  # 会话数量
    }
```

---

### 第 10 步：启动服务器

```python
# if __name__ == "__main__": 是 Python 的入口判断
# 只有直接运行这个文件时才执行，import 时不执行
if __name__ == "__main__":
    # 导入 uvicorn（ASGI 服务器，类似 Nginx + Gunicorn）
    import uvicorn
    
    # 打印启动信息
    print("=" * 50)
    print("🚀 AI Agent Web Chat 服务器")
    print("=" * 50)
    print(f"📍 访问地址：http://localhost:8000")
    print(f"📍 API 文档：http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 启动服务器
    # app: FastAPI 应用
    # host="0.0.0.0": 监听所有网络接口（局域网可访问）
    # port=8000: 端口号
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**运行方式对比**：
```bash
# 方式 1：直接运行（使用上面的代码）
python web_chat.py

# 方式 2：用 uvicorn 命令（更灵活）
uvicorn web_chat:app --host 0.0.0.0 --port 8000 --reload

# --reload: 代码变化自动重启（开发用）
```

---

## 第二部分：前端代码详解（web/chat.html）

### 第 1 步：HTML 结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <!-- viewport: 移动端适配关键，让页面宽度等于设备宽度 -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI Agent Chat</title>
    
    <!-- 引入 marked.js：Markdown 渲染库 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <!-- 引入 highlight.js：代码高亮库 -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css">
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/core.min.js"></script>
</head>
<body>
    <!-- 应用容器 -->
    <div class="app-container">
        <!-- 头部：标题 + 模型选择 -->
        <header class="header">...</header>
        
        <!-- 聊天区域：显示消息 -->
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <!-- 消息会动态添加到这里 -->
            </div>
        </div>
        
        <!-- 输入区域：文本框 + 发送按钮 -->
        <div class="input-container">
            <textarea id="user-input"></textarea>
            <button id="send-btn" onclick="sendMessage()">发送</button>
        </div>
    </div>
</body>
</html>
```

---

### 第 2 步：CSS 样式（响应式设计）

```css
/* CSS 变量：统一管理颜色，方便换主题 */
:root {
    --primary-color: #667eea;
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --bg-color: #f5f7fa;
}

/* 基础重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;  /* 边框计入宽度，布局更直观 */
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", ...;  /* 系统字体 */
    background: var(--bg-color);
    min-height: 100vh;  /* 至少占满整个屏幕高度 */
}

/* 弹性布局：让应用占满屏幕 */
.app-container {
    display: flex;
    flex-direction: column;  /* 垂直排列：头 - 聊天 - 输入 */
    height: 100vh;
}

/* 聊天区域：可滚动 */
.chat-container {
    flex: 1;  /* 占据剩余空间 */
    overflow-y: auto;  /* 垂直滚动 */
}

/* 消息气泡 */
.message {
    display: flex;
    max-width: 85%;  /* 不要太宽，阅读舒适 */
    animation: slideIn 0.3s ease;  /* 滑入动画 */
}

/* 用户消息靠右 */
.message.user {
    align-self: flex-end;
    flex-direction: row-reverse;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .header {
        padding: 12px 16px;  /* 减小内边距 */
    }
    
    .message {
        max-width: 90%;  /* 消息更宽 */
    }
}
```

**响应式设计关键**：
```css
/* 媒体查询：屏幕宽度小于 768px 时应用不同样式 */
@media (max-width: 768px) {
    /* 移动端样式 */
}
```

---

### 第 3 步：JavaScript 核心逻辑

```javascript
// ========== 配置 ==========
// API 服务器地址
const API_BASE_URL = 'http://localhost:8000';

// 会话 ID：用 localStorage 持久化，刷新页面不丢失
// localStorage: 浏览器本地存储，类似小型数据库
const sessionId = localStorage.getItem('agent_session_id') || 'session_' + Date.now();
localStorage.setItem('agent_session_id', sessionId);


// ========== 发送消息 ==========
async function sendMessage() {
    // 获取输入框和消息内容
    const input = document.getElementById('user-input');
    const message = input.value.trim();  // 去除首尾空格
    
    // 空消息不发送
    if (!message) return;
    
    // 1. 在界面上显示用户消息
    addMessage(message, 'user');
    
    // 2. 清空输入框
    input.value = '';
    
    // 3. 禁用输入（防止重复发送）
    setSendButton(false);
    showTyping(true);  // 显示"正在思考..."
    
    // 4. 获取选中的模型
    const model = document.getElementById('model-select').value;
    
    // 5. 发送请求到后端
    try {
        // fetch: 浏览器内置的 HTTP 请求函数
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',  // HTTP 方法
            headers: {
                'Content-Type': 'application/json'  // 请求体是 JSON
            },
            body: JSON.stringify({  // 把对象转为 JSON 字符串
                session_id: sessionId,
                message: message,
                model: model
            })
        });
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`请求失败：${response.status}`);
        }
        
        // 解析 JSON 响应
        const data = await response.json();
        
        // 6. 显示 AI 回复
        showTyping(false);
        addMessage(data.reply, 'agent');
        
    } catch (error) {
        // 错误处理
        showTyping(false);
        addMessage(`❌ 错误：${error.message}`, 'agent');
        console.error('Chat error:', error);  // 打印到控制台（调试用）
    } finally {
        // 无论成功失败，都恢复输入
        setSendButton(true);
    }
}


// ========== 添加消息到界面 ==========
function addMessage(content, type) {
    const messagesContainer = document.getElementById('chat-messages');
    
    // 创建消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;  // 如 "message user"
    
    const avatar = type === 'user' ? '👤' : '🤖';
    
    let innerHTML;
    if (type === 'agent') {
        // AI 消息：渲染 Markdown
        innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="message-content">
                <markdown>${renderMarkdown(content)}</markdown>
            </div>
        `;
    } else {
        // 用户消息：纯文本（防止 XSS 攻击）
        innerHTML = `
            <div class="message-content">${escapeHtml(content)}</div>
            <div class="avatar">${avatar}</div>
        `;
    }
    
    messageDiv.innerHTML = innerHTML;
    messagesContainer.appendChild(messageDiv);  // 添加到页面
    scrollToBottom();  // 滚动到底部
}


// ========== Markdown 渲染 ==========
function renderMarkdown(text) {
    // marked.parse(): 把 Markdown 转为 HTML
    const html = marked.parse(text);
    
    // 代码高亮：等元素添加后再处理
    setTimeout(() => {
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);  // highlight.js 高亮
        });
    }, 0);
    
    return html;
}


// ========== HTML 转义（防止 XSS）==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;  // 纯文本（自动转义 < > & 等）
    return div.innerHTML;  // 获取转义后的 HTML
}


// ========== 键盘事件 ==========
function handleKeyDown(event) {
    // Enter 发送，Shift+Enter 换行
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();  // 阻止默认换行
        sendMessage();
    }
}
```

---

## 第三部分：完整请求流程

```
1. 用户在输入框输入"北京天气怎么样？"
   ↓
2. 按 Enter，触发 handleKeyDown() → sendMessage()
   ↓
3. 前端显示用户消息（addMessage）
   ↓
4. fetch POST /chat，发送 JSON:
   {
     "session_id": "session_123",
     "message": "北京天气怎么样？",
     "model": "qwen3.5-plus"
   }
   ↓
5. 后端接收请求，解析为 ChatRequest 对象
   ↓
6. 获取会话历史，添加用户消息
   ↓
7. 调用阿里云 API:
   client.chat.completions.create(...)
   ↓
8. LLM 返回：需要调用 get_weather 工具
   ↓
9. 后端执行 TOOLS["get_weather"](city="北京")
   ↓
10. 把工具结果返回给 LLM
    ↓
11. LLM 生成最终回复："北京现在 25°C，晴天"
    ↓
12. 后端返回 JSON 响应
    ↓
13. 前端接收响应，渲染 Markdown
    ↓
14. 显示 AI 回复，滚动到底部
```

---

## 📝 学习建议

### 第一天：理解后端
1. 阅读 `web_chat.py` 每行注释
2. 在 `/docs` 页面查看自动生成的 API 文档
3. 用 curl 测试 API：
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id":"test","message":"你好"}'
   ```

### 第二天：理解前端
1. 打开浏览器开发者工具（F12）
2. 在 Network 标签看请求/响应
3. 在 Console 尝试调用函数：`sendMessage()`

### 第三天：动手修改
1. 修改欢迎消息
2. 添加新工具
3. 改变主题颜色（改 CSS 变量）

---

有问题随时问！🚀
