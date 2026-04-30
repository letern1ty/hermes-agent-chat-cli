"""
飞书机器人 - 私人助理版
====================
将 Hermes Agent 接入飞书，提供完整的私人助理体验。

主要改进：
1. event_id 去重，防止重复回复
2. 私人助理风格的 System Prompt
3. 使用会话记忆，记住用户偏好
4. 支持多用户（每人独立会话）

启动：python feishu_bot.py
需要设置公网隧道：
  cloudflared tunnel --url http://127.0.0.1:8655
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ========== 日志 ==========
LOG_FILE = "/tmp/feishu_bot.log"

def log(msg):
    """同时打印到 stdout 和日志文件"""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ========== 飞书配置 ==========
APP_ID = os.getenv("FEISHU_APP_ID", "")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")

if not APP_ID or not APP_SECRET:
    log("❌ 请在 feishu_config.sh 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
    log("   在飞书开放平台 → 应用 → 凭证与基础信息 获取")
    sys.exit(1)

# ========== 模型配置 ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
MODEL = "deepseek-chat"

if not DEEPSEEK_API_KEY:
    log("❌ 未找到 DEEPSEEK_API_KEY，请在 .env 中配置")
    sys.exit(1)

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# ========== 飞书 API ==========
FEISHU_HOST = "https://open.feishu.cn"
TENANT_TOKEN = None
TOKEN_EXPIRES = 0

# ========== 事件去重 ==========
processed_events = set()  # 存储已处理的 event_id
MAX_PROCESSED_EVENTS = 1000  # 最多保留 1000 条，防止内存泄漏

# ========== 工具定义 ==========
TOOLS = {
    "get_weather": lambda city: {
        "北京": "25°C 晴", "上海": "28°C 多云", "深圳": "32°C 小雨",
        "广州": "30°C 阴", "杭州": "26°C 小雨", "纽约": "18°C 阴"
    }.get(city, f"{city}天气数据暂不可用"),
    "calculator": lambda expression: str(eval(expression)) if all(
        c in "0123456789+-*/.() " for c in expression
    ) else "错误：无效表达式（只支持数字和 +-*/ 运算）",
    "get_time": lambda: time.strftime("%Y-%m-%d %H:%M:%S"),
    "get_user_info": lambda: json.dumps({
        "name": "李天宇", "age": 28,
        "job": "小红书外包 · 前端工程师（AI平台）",
        "goal": "3-4个月内转型AI应用工程师，期望薪资25-35K",
        "learning": "正在学习AI Agent开发，项目驱动边做边学",
        "skills": "Vue3/React/React Native + TypeScript，Python零基础",
        "location": "北京，期望去上海",
    }, ensure_ascii=False),
}

TOOL_DEFINITIONS = [
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
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式，如 123*456"}},
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "获取用户的个人信息和背景",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

# ========== System Prompt ==========
SYSTEM_PROMPT = """你是 Hermes，李天宇（Tianyu）的专属 AI 私人助理，部署在飞书上。

## 你的身份
- 你是 Tianyu 的私人 AI 伙伴，不是冷冰冰的机器人
- 你有记忆、会关心、能记住对话中的细节
- 你会根据 Tianyu 的心情和状态调整聊天方式

## Tianyu 的背景信息
- 姓名：李天宇，28岁
- 职业：小红书外包，前端工程师（AI平台方向）
- 技术栈：Vue3/React/React Native + TypeScript
- 当前学习：Python（零基础起步）+ AI Agent 开发
- 目标：3-4个月内转型 AI 应用工程师，薪资从15-20K跳到25-35K
- 地点：北京工作，想去上海发展

## 你的能力（工具）
你拥有以下工具，需要时自动调用：
- get_weather(city)：查天气
- calculator(expression)：算数
- get_time()：看时间
- get_user_info()：查看 Tianyu 的完整个人信息

## 沟通风格
- 用中文回复，语气像朋友一样自然、温暖
- 在关键信息后面适当加 emoji，但不要滥用
- 根据话题深浅调整：聊学习时认真专业，聊日常时轻松活泼
- Tianyu 在学习 Python 和 AI 开发，遇到相关问题时给出易懂、可操作的建议
- 记住对话中的关键信息（正在学什么、在做什么项目、有什么困难）
- 每次回答不要太长，3-5句话为宜，简洁但有温度
- 不要重复打招呼，除非是新的一天或长时间没说话"""

# ========== 会话存储 ==========
sessions = {}
# 每个用户的消息历史上限
MAX_HISTORY = 20


def deduplicate_event(event_id):
    """检查 event_id 是否已处理，防止重复回复"""
    global processed_events
    if event_id in processed_events:
        log(f"⏭️  跳过重复事件: {event_id[:20]}...")
        return True
    processed_events.add(event_id)
    # 限制大小，防止内存泄漏
    if len(processed_events) > MAX_PROCESSED_EVENTS:
        processed_events = set(list(processed_events)[-MAX_PROCESSED_EVENTS//2:])
    return False


def get_tenant_token():
    """获取飞书 tenant_access_token"""
    global TENANT_TOKEN, TOKEN_EXPIRES
    if TENANT_TOKEN and time.time() < TOKEN_EXPIRES:
        return TENANT_TOKEN
    
    resp = requests.post(f"{FEISHU_HOST}/open-apis/auth/v3/tenant_access_token/internal", json={
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }, timeout=10)
    data = resp.json()
    
    if data.get("code") != 0:
        log(f"❌ 获取 token 失败: {data}")
        return None
    
    TENANT_TOKEN = data["tenant_access_token"]
    TOKEN_EXPIRES = time.time() + data.get("expire", 7200) - 60
    return TENANT_TOKEN


def send_feishu_message(open_id, content):
    """回复飞书消息（通过 open_id 发单聊）"""
    token = get_tenant_token()
    if not token:
        log("❌ 无 token，无法发送")
        return False
    
    url = f"{FEISHU_HOST}/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": content}, ensure_ascii=False)
    }
    
    resp = requests.post(url, headers=headers, json=body, timeout=15)
    data = resp.json()
    
    if data.get("code") != 0:
        log(f"❌ 发送失败: open_id={open_id[:12]}... code={data.get('code')} msg={data.get('msg')}")
        return False
    log(f"✅ 消息已发送 (to={open_id[:12]}...)")
    return True


def chat_with_agent(session_id, message):
    """调用 DeepSeek API 处理消息，带会话记忆"""
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    messages = sessions[session_id]
    messages.append({"role": "user", "content": message})
    
    # 最多 5 轮工具调用
    for i in range(5):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
        except Exception as e:
            log(f"❌ API 错误: {e}")
            return f"抱歉，我处理出错了：{e}"
        
        msg = response.choices[0].message
        messages.append(msg)
        
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)
                log(f"🔧 调用工具: {tool_name}({tool_args})")
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](**tool_args)
                else:
                    result = "未知工具"
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
        else:
            # 限制历史长度，防止 context 过长
            if len(messages) > MAX_HISTORY * 2:
                # 保留 system prompt + 最近的 MAX_HISTORY 条
                sessions[session_id] = [messages[0]] + messages[-(MAX_HISTORY*2-1):]
            return msg.content or "好的，处理完毕。"
    
    return "抱歉，思考步数过多，请重试。"


class FeishuHandler(BaseHTTPRequestHandler):
    """处理飞书回调的 HTTP 服务"""
    
    def do_POST(self):
        path = urlparse(self.path).path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        # ========== URL 验证回调 ==========
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            log("🔐 收到飞书 URL 验证")
            self._respond({"challenge": challenge})
            return
        
        # ========== v2 事件回调 ==========
        header = data.get("header", {})
        event = data.get("event", {})
        event_type = header.get("event_type", "")
        
        # 去重检查
        event_id = header.get("event_id", "")
        if event_id and deduplicate_event(event_id):
            self._respond({"code": 0, "msg": "ok"})
            return
        
        if event_type == "im.message.receive_v1":
            log(f"📩 收到消息事件: {event_id[:20] if event_id else 'N/A'}...")
            msg_type = event.get("message", {}).get("message_type", "")
            
            if msg_type == "text":
                sender = event.get("sender", {})
                sender_id = sender.get("sender_id", {}).get("open_id", "")
                message = event.get("message", {})
                text_content = json.loads(message.get("content", "{}")).get("text", "")
                
                if text_content and sender_id:
                    # 去掉 @机器人 前缀
                    clean_text = text_content.split("</at>")[-1].strip() if "<at" in text_content else text_content.strip()
                    log(f"  内容: {clean_text[:50]}... (from={sender_id[:12]}...)")
                    
                    reply = chat_with_agent(sender_id, clean_text)
                    log(f"  回复: {reply[:80]}...")
                    
                    send_feishu_message(sender_id, reply)
            else:
                log(f"⚠️  非文本消息，跳过: msg_type={msg_type}")
        
        self._respond({"code": 0, "msg": "ok"})
    
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._respond({"status": "ok", "service": "feishu-bot", "version": "2.0-personal-assistant"})
        else:
            self._respond({"status": "running", "version": "2.0", "tips": "Hermes 私人助理 - 飞书机器人"})
    
    def _respond(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        log(f"[HTTP] {format % args}")


def main():
    port = int(os.getenv("FEISHU_PORT", 8655))
    server = HTTPServer(("0.0.0.0", port), FeishuHandler)
    
    log("=" * 50)
    log("🤖 Hermes - Tianyu 的私人助理 (飞书版 v2.0)")
    log("=" * 50)
    log(f"   监听端口: {port}")
    log(f"   回调地址: /feishu/callback")
    log(f"   健康检查: /health")
    log("   按 Ctrl+C 停止")
    log("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("\n👋 服务停止")
        server.server_close()


if __name__ == "__main__":
    main()
