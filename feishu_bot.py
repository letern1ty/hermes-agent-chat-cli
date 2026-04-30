"""
飞书机器人服务
============
接收飞书消息，转发给 Hermes Agent，回复到飞书

流程：
1. 飞书用户发消息 → 飞书平台回调 → 本服务
2. 本服务验证签名，解析消息
3. 调用 DeepSeek API 处理（同 Hermes Agent）
4. 回复到飞书

启动：python feishu_bot.py
回调地址需要配成公网可访问：
  cloudflared tunnel --url http://localhost:8655
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

# ========== 工具定义 ==========
TOOLS = {
    "get_weather": lambda city: {
        "北京": "25°C 晴", "上海": "28°C 多云", "深圳": "32°C 小雨",
        "广州": "30°C 阴", "杭州": "26°C 小雨", "纽约": "18°C 阴"
    }.get(city, f"{city}天气数据暂不可用"),
    "calculator": lambda expression: str(eval(expression)) if all(c in "0123456789+-*/.() " for c in expression) else "错误：无效表达式",
    "get_time": lambda: time.strftime("%Y-%m-%d %H:%M:%S")
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
    }
]

SYSTEM_PROMPT = """你是 Hermes AI Agent，部署在飞书上的智能助手。
你可以使用工具来回答问题：
- get_weather(city): 查询城市天气
- calculator(expression): 计算数学表达式
- get_time(): 获取当前时间

请用中文回复，语气友好、简洁。"""

# 会话存储
sessions = {}


def get_tenant_token():
    """获取飞书 tenant_access_token"""
    global TENANT_TOKEN, TOKEN_EXPIRES
    if TENANT_TOKEN and time.time() < TOKEN_EXPIRES:
        return TENANT_TOKEN
    
    url = f"{FEISHU_HOST}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
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


def send_feishu_message(chat_id, content):
    """回复飞书消息"""
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
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": content}, ensure_ascii=False)
    }
    
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    data = resp.json()
    
    if data.get("code") != 0:
        log(f"❌ 发送消息失败: chat_id={chat_id[:20]}... code={data.get('code')} msg={data.get('msg')}")
        return False
    log(f"✅ 消息已发送 (chat_id={chat_id[:20]}...)")
    return True


def chat_with_agent(session_id, message):
    """调用 DeepSeek API 处理消息"""
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
        
        # ========== 飞书 URL 验证回调 (新版也用 schema/header 格式) ==========
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            log("🔐 收到飞书 URL 验证")
            self._respond({"challenge": challenge})
            return
        
        # 检查是否是事件回调（v2 新格式）
        header = data.get("header", {})
        event = data.get("event", {})
        
        if header.get("event_type") == "im.message.receive_v1":
            log(f"📦 收到 v2 事件: {header.get('event_id', '')[:20]}...")
            msg_type = event.get("message", {}).get("message_type", "")
            
            if msg_type == "text":
                sender = event.get("sender", {})
                sender_id = sender.get("sender_id", {}).get("open_id", "")
                message = event.get("message", {})
                chat_id = message.get("chat_id", "")
                text_content = json.loads(message.get("content", "{}")).get("text", "")
                
                if text_content and sender_id:
                    clean_text = text_content.split("</at>")[-1].strip() if "<at" in text_content else text_content.strip()
                    log(f"📩 收到飞书消息: {clean_text[:50]}... (from={sender_id[:12]}...)")
                    
                    reply = chat_with_agent(sender_id, clean_text)
                    log(f"💬 Agent 回复: {reply[:80]}...")
                    
                    send_feishu_message(sender_id, reply)  # 用 sender_id (open_id) 回复单聊
            else:
                log(f"⚠️  非文本消息，跳过: msg_type={msg_type}")
        else:
            log(f"📦 收到其他回调: header_keys={list(header.keys()) if header else 'N/A'}")
        
        self._respond({"code": 0, "msg": "ok"})
    
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._respond({"status": "ok", "service": "feishu-bot"})
        else:
            self._respond({"status": "running", "tips": "飞书机器人服务运行中"})
    
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
    log("🤖 Hermes Agent - 飞书机器人")
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
