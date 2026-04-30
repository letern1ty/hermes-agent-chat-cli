"""
飞书机器人 - 从零到私人助理 : 完整学习版
=========================================
学习目标：理解如何将 AI Agent 接入飞书聊天，并一步步提升它的能力

版本历史：
  v1.0 - 基础版：接收飞书消息 -> 调 DeepSeek API -> 回复
  v2.0 - 私人助理版：事件去重、专属 Prompt、会话记忆

运行方式：
  1. 启动服务:  python feishu_bot.py
  2. 启动隧道:  cloudflared tunnel --url http://127.0.0.1:8655
  3. 配置回调:  飞书开放平台 -> 事件与回调 -> 填入隧道 URL/feishu/callback

依赖安装：
  pip install requests openai python-dotenv
"""

# ====================================================================
# 模块 1：导入 - 你用什么库，为什么用
# ====================================================================
# json:    解析飞书发来的 JSON 数据，以及序列化回复内容
# os:      读取环境变量（API Key、飞书配置等敏感信息）
# sys:     当配置缺失时退出程序 (sys.exit)
# time:    获取当前时间、管理 token 过期时间
# http.server: Python 内置 HTTP 服务器，不需要 Flask/FastAPI，减少依赖
# urllib.parse: 解析 URL 路径（区分 /feishu/callback 和 /health）
# requests: 发送 HTTP 请求到飞书 API 和 DeepSeek API
# openai:  DeepSeek API 兼容 OpenAI 格式，所以用 OpenAI 库调用

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import requests
from openai import OpenAI
from dotenv import load_dotenv

# ====================================================================
# 模块 1.5：个人信息 - 为什么单独放一个文件？
# ====================================================================
# 知识点：
# - 把个人信息（姓名、职业、目标）放到独立的 user_profile.py
# - user_profile.py 在 .gitignore 中排除，不会提交到 Git
# - 公开仓库里只有 user_profile.example.py（模板，不含真实信息）
# - 这样面试官看代码时不会看到你的隐私，但 AI 助理依然能个性化回答
# - 如果你想改 AI 对你的称呼、职业信息，只需改 user_profile.py
import importlib.util
import os
_profile_path = os.path.join(os.path.dirname(__file__), "user_profile.py")
_spec = importlib.util.spec_from_file_location("user_profile", _profile_path)
_profile = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_profile)
USER_NAME = _profile.USER_NAME
USER_AGE = _profile.USER_AGE
USER_JOB = _profile.USER_JOB
USER_GOAL = _profile.USER_GOAL
USER_SKILLS = _profile.USER_SKILLS
USER_LOCATION = _profile.USER_LOCATION
ASSISTANT_NAME = _profile.ASSISTANT_NAME
USER_NICKNAME = _profile.USER_NICKNAME
USER_EXTRA_CONTEXT = _profile.USER_EXTRA_CONTEXT

load_dotenv()  # 读取 .env 文件中的环境变量

# ====================================================================
# 模块 2：日志 - 为什么要写文件日志？
# ====================================================================
# 关键知识点：
# 当服务通过 terminal(background=true) 启动时，print() 的输出
# 不会被捕获到。所以一定要同时写文件，否则出了问题完全不知道
# 发生了什么。
# 调试飞书机器人时，80% 的问题靠看日志就能定位。
LOG_FILE = "/tmp/feishu_bot.log"

def log(msg):
    """同时打印到 stdout 和日志文件，确保后台运行时也能追踪"""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)  # flush=True 确保立即输出
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass  # 文件写失败不影响主流程

# ====================================================================
# 模块 3：飞书配置 - 敏感信息放在哪里？
# ====================================================================
# 知识点：
# - 永远不要把 API Key / App Secret 写在代码里
# - 用环境变量（.env 文件或 shell export）来管理敏感信息
# - feishu_config.sh 里 export 了飞书配置，运行时 source 它
# - .env 里放了 DeepSeek API Key
# - 两个文件都不提交到 Git（在 .gitignore 中配置）

APP_ID = os.getenv("FEISHU_APP_ID", "")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")

# ========== 启动时检查配置 ==========
# 如果配置缺失，立即报错退出。免得运行时出诡异问题
if not APP_ID or not APP_SECRET:
    log("❌ 请在 feishu_config.sh 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
    log("   在飞书开放平台 → 应用 → 凭证与基础信息 获取")
    sys.exit(1)

# ====================================================================
# 模块 4：LLM 配置 - 为什么用 OpenAI 库调 DeepSeek？
# ====================================================================
# 知识点：DeepSeek API 完全兼容 OpenAI 的接口格式
# 所以只需要改 base_url 和 api_key，就能用 OpenAI 的 Python SDK
# 调用 DeepSeek。这是一种常见的"兼容模式"。

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
MODEL = "deepseek-chat"

if not DEEPSEEK_API_KEY:
    log("❌ 未找到 DEEPSEEK_API_KEY，请在 .env 中配置")
    sys.exit(1)

# 创建 OpenAI 客户端，但指向 DeepSeek 的 API 地址
# base_url 要改成 DeepSeek 的地址：https://api.deepseek.com
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# ====================================================================
# 模块 5：飞书 API 通信 - 为什么要拿 token？
# ====================================================================
# 飞书的所有 API 都需要 tenant_access_token 进行身份验证
# 就像你去办事要先拿个号（token），然后用这个号去办具体业务
# token 有过期时间（2小时），到期后需要重新获取
FEISHU_HOST = "https://open.feishu.cn"  # 飞书开放平台 API 域名
TENANT_TOKEN = None    # 缓存 token，避免每次都重新获取
TOKEN_EXPIRES = 0      # token 过期时间戳

# ====================================================================
# 模块 6：事件去重 - 为什么飞书会发重复消息？
# ====================================================================
# 飞书为了保证消息不丢失，会尝试重试推送
# 如果你的服务在 2 秒内没有返回 200，飞书会再发一次
# 如果不做去重，用户就会收到两条回复
#
# 解决方案：每个事件都有一个唯一的 event_id
# 每次处理前检查 event_id 是否已处理过，跳过重复的
processed_events = set()
MAX_PROCESSED_EVENTS = 1000  # 内存限制，防止无限增长

# ====================================================================
# 模块 7：工具定义 - 什么是 Function Calling？
# ====================================================================
# 这是让 AI "动手做事"的核心机制。
#
# 原理：
# 1. 你定义一堆工具（函数），告诉 AI 每个工具叫什么、做什么用、需要什么参数
# 2. AI 根据用户的问题，决定要不要调用工具、调哪个、传什么参数
# 3. AI 返回的响应里会说"我想调 get_weather，参数是 city='北京'"
# 4. 你的代码执行这个函数，把结果塞回给 AI
# 5. AI 看到结果后组织成自然语言回复给用户
#
# 这就是所谓的"Function Calling"或"Tool Use"
# 注意：lambda 参数名必须和 TOOL_DEFINITIONS 中定义的一致！
# 如果定义的是 "city"，lambda 就要写 lambda city: ... 不能写 lambda c:

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
        "name": USER_NAME, "age": USER_AGE,
        "job": USER_JOB,
        "goal": USER_GOAL,
        "learning": USER_EXTRA_CONTEXT,
        "skills": USER_SKILLS,
        "location": USER_LOCATION,
    }, ensure_ascii=False),
}

# TOOL_DEFINITIONS 是给 AI 看的"工具说明书"
# AI 根据这些描述来决定何时调用哪个工具
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

# ====================================================================
# 模块 8：System Prompt - 怎么让 AI 有"人设"？
# ====================================================================
# System Prompt 是给 AI 的"角色说明书"
# 它定义了 AI 的身份、说话方式、行为准则
# 写好 System Prompt 是调教 AI 最关键的一步
#
# 写 System Prompt 的经验：
# - 具体比抽象好（"用朋友语气打招呼" ✓ vs "友好一些" ✗）
# - 给明确的规则边界（"每次回答3-5句话" 比 "不要太长" 好）
# - 把用户背景写进去，AI 就能提供更个性化的回答
# - 列出所有工具的用途，但不要限制 AI 使用它们的方式

SYSTEM_PROMPT = f"""你是 {ASSISTANT_NAME}，{USER_NICKNAME}（{USER_NAME}）的专属 AI 私人助理，部署在飞书上。

## 你的身份
- 你是 {USER_NICKNAME} 的私人 AI 伙伴，不是冷冰冰的机器人
- 你有记忆、会关心、能记住对话中的细节
- 你会根据 {USER_NICKNAME} 的心情和状态调整聊天方式

## {USER_NICKNAME} 的背景信息
- 姓名：{USER_NAME}，{USER_AGE}岁
- 职业：{USER_JOB}
- 技术栈：{USER_SKILLS}
- 当前学习：{USER_EXTRA_CONTEXT}
- 目标：{USER_GOAL}
- 地点：{USER_LOCATION}

## 你的能力（工具）
你拥有以下工具，需要时自动调用：
- get_weather(city)：查天气
- calculator(expression)：算数
- get_time()：看时间
- get_user_info()：查看 {USER_NICKNAME} 的完整个人信息

## 沟通风格
- 用中文回复，语气像朋友一样自然、温暖
- 在关键信息后面适当加 emoji，但不要滥用
- 根据话题深浅调整：聊学习时认真专业，聊日常时轻松活泼
- {USER_NICKNAME} 在学习 Python 和 AI 开发，遇到相关问题时给出易懂、可操作的建议
- 记住对话中的关键信息（正在学什么、在做什么项目、有什么困难）
- 每次回答不要太长，3-5句话为宜，简洁但有温度
- 不要重复打招呼，除非是新的一天或长时间没说话"""

# ====================================================================
# 模块 9：会话管理 - 怎么让 AI "记住"上下文？
# ====================================================================
# AI 本身没有记忆——它每次只根据当前的对话历史来回复
# "记忆"其实就是把历史消息存起来，每次请求时一起发给 AI
#
# sessions 的 key 是用户的 open_id（飞书用户唯一标识）
# 这样不同用户有各自独立的会话，互不干扰
# 每个会话是一个消息列表：[{role, content}, ...]
sessions = {}
MAX_HISTORY = 20  # 最多保留最近 20 轮对话，防止 token 超长

# ====================================================================
# 模块 10：核心函数 - 每段代码在做什么
# ====================================================================

def deduplicate_event(event_id):
    """
    检查事件是否已处理过。
    飞书可能因网络重试重复推送同一事件，
    如果不做去重，用户会收到多条同样的回复。
    """
    global processed_events
    if event_id in processed_events:
        log(f"⏭️  跳过重复事件: {event_id[:20]}...")
        return True
    processed_events.add(event_id)
    # 控制集合大小，防止内存无限增长
    if len(processed_events) > MAX_PROCESSED_EVENTS:
        processed_events = set(list(processed_events)[-MAX_PROCESSED_EVENTS//2:])
    return False


def get_tenant_token():
    """
    获取飞书 tenant_access_token。
    这是飞书 API 的身份凭证，相当于"访问令牌"。
    过期时间 2 小时，过期后需要重新获取。
    这里做了缓存，避免每次发送消息时都去拿 token。
    """
    global TENANT_TOKEN, TOKEN_EXPIRES
    # 缓存有效，直接返回
    if TENANT_TOKEN and time.time() < TOKEN_EXPIRES:
        return TENANT_TOKEN
    
    # 用 App ID + App Secret 换取 token
    resp = requests.post(f"{FEISHU_HOST}/open-apis/auth/v3/tenant_access_token/internal", json={
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }, timeout=10)
    data = resp.json()
    
    if data.get("code") != 0:
        log(f"❌ 获取 token 失败: {data}")
        return None
    
    TENANT_TOKEN = data["tenant_access_token"]
    # 提前 60 秒过期，防止边界情况
    TOKEN_EXPIRES = time.time() + data.get("expire", 7200) - 60
    return TENANT_TOKEN


def send_feishu_message(open_id, content):
    """
    回复飞书消息。
    用 open_id（用户唯一标识）发送单聊消息。
    注意：v1 版本用的是 chat_id（群聊ID）导致发送失败，
    单聊应该用 open_id 作为 receive_id。
    """
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
        "msg_type": "text",  # 文本消息
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
    """
    核心函数：用 DeepSeek API 处理消息。
    
    流程：
    1. 如果用户是第一次说话，创建新的会话（含 System Prompt）
    2. 把用户消息追加到会话历史
    3. 调用 DeepSeek API，带上所有历史消息和工具定义
    4. 如果 AI 想调用工具 → 执行工具 → 把结果塞回去 → 让 AI 继续
    5. 如果 AI 直接回复了文字 → 返回给用户
    
    这就是"ReAct"的简化版：思考 -> 行动 -> 观察 -> 思考...
    最多循环 5 轮防止死循环。
    """
    if session_id not in sessions:
        # 新用户，用 System Prompt 初始化会话
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    messages = sessions[session_id]
    messages.append({"role": "user", "content": message})
    
    for i in range(5):  # 最多 5 轮工具调用
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,    # 告诉 AI 有哪些工具可用
                tool_choice="auto"         # AI 自己决定要不要用工具
            )
        except Exception as e:
            log(f"❌ API 错误: {e}")
            return f"抱歉，我处理出错了：{e}"
        
        msg = response.choices[0].message
        messages.append(msg)
        
        if msg.tool_calls:
            # ========== AI 决定调用工具 ==========
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)
                log(f"🔧 调用工具: {tool_name}({tool_args})")
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](**tool_args)
                else:
                    result = "未知工具"
                # 把工具执行结果塞回给 AI，让 AI 根据结果组织回答
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
            # 继续循环，AI 可能还要调用更多工具，或者已经够信息来回答了
        else:
            # ========== AI 直接回复文字 ==========
            # 限制会话历史长度（防 token 超长和费用过高）
            if len(messages) > MAX_HISTORY * 2:
                sessions[session_id] = [messages[0]] + messages[-(MAX_HISTORY*2-1):]
            return msg.content or "好的，处理完毕。"
    
    return "抱歉，思考步数过多，请重试。"

# ====================================================================
# 模块 11：HTTP 服务 - Python 内置的服务器怎么用？
# ====================================================================
# HTTPServer 是 Python 自带的 HTTP 服务器
# 不需要 Flask/FastAPI，零依赖就能跑一个 Web 服务
#
# 优点：零依赖、轻量
# 缺点：同步处理（一个请求没处理完，下一个要等）
# 对于飞书机器人来说足够了，因为 DeepSeek API 调用才是瓶颈
#
# BaseHTTPRequestHandler 是一个请求处理器类
# 你只需要重写 do_GET() 和 do_POST() 方法
# 系统会自动把不同的 HTTP 方法路由到这里

class FeishuHandler(BaseHTTPRequestHandler):
    """处理飞书回调的 HTTP 服务"""
    
    def do_POST(self):
        """
        处理 POST 请求（飞书回调）
        
        飞书会发两种 POST 请求：
        1. URL 验证（配置回调地址时触发）
        2. 消息事件（用户发消息时触发）
        
        新版飞书（v2）使用 header/event 格式：
        {
            "schema": "2.0",
            "header": {"event_id": "...", "event_type": "im.message.receive_v1"},
            "event": {...}
        }
        """
        # 步骤 1：读取请求体
        # Content-Length 告诉我们应该读多少字节
        path = urlparse(self.path).path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        
        # 步骤 2：解析 JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        # 步骤 3：判断回调类型
        # 旧版：type == "url_verification"
        # 新版：header.event_type == "im.message.receive_v1"
        
        # ========== URL 验证 ==========
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            log("🔐 收到飞书 URL 验证")
            self._respond({"challenge": challenge})
            return
        
        # ========== v2 事件回调处理 ==========
        header = data.get("header", {})
        event = data.get("event", {})
        event_type = header.get("event_type", "")
        
        # 去重检查 - 防止飞书重试导致重复回复
        event_id = header.get("event_id", "")
        if event_id and deduplicate_event(event_id):
            self._respond({"code": 0, "msg": "ok"})
            return
        
        # ========== 处理消息事件 ==========
        if event_type == "im.message.receive_v1":
            log(f"📩 收到消息事件: {event_id[:20] if event_id else 'N/A'}...")
            msg_type = event.get("message", {}).get("message_type", "")
            
            # 目前只处理文本消息，图片/文件等需要额外开发
            if msg_type == "text":
                sender = event.get("sender", {})
                sender_id = sender.get("sender_id", {}).get("open_id", "")
                message = event.get("message", {})
                # 文本内容藏在 content 字段里，而且是 JSON 字符串
                text_content = json.loads(message.get("content", "{}")).get("text", "")
                
                if text_content and sender_id:
                    # 去掉 @机器人 前缀（群聊中 @机器人时会有 <at...></at> 标签）
                    clean_text = text_content.split("</at>")[-1].strip() if "<at" in text_content else text_content.strip()
                    log(f"  内容: {clean_text[:50]}... (from={sender_id[:12]}...)")
                    
                    # 核心：调用 AI 处理
                    reply = chat_with_agent(sender_id, clean_text)
                    log(f"  回复: {reply[:80]}...")
                    
                    # 发回给用户
                    send_feishu_message(sender_id, reply)
            else:
                log(f"⚠️  非文本消息，跳过: msg_type={msg_type}")
        
        # 步骤 4：返回 200 给飞书，表示收到
        self._respond({"code": 0, "msg": "ok"})
    
    def do_GET(self):
        """处理 GET 请求（健康检查 + 状态页）"""
        path = urlparse(self.path).path
        if path == "/health":
            self._respond({"status": "ok", "service": "feishu-bot", "version": "2.0-personal-assistant"})
        else:
            self._respond({"status": "running", "version": "2.0", "tips": "Hermes 私人助理 - 飞书机器人"})
    
    def _respond(self, data, status=200):
        """
        统一的 JSON 响应方法
        - 设置正确的 Content-Type（带 charset=utf-8 防止中文乱码）
        - 设置 Content-Length（HTTP 协议要求）
        - 写入响应体
        """
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        """重写默认日志，把 HTTP 日志也写到我们的文件日志里"""
        log(f"[HTTP] {format % args}")


def main():
    """
    程序入口点。
    启动 HTTP 服务器，监听 8655 端口。
    端口号可以通过环境变量 FEISHU_PORT 配置。
    """
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


# ====================================================================
# Python 的标准入口写法
# 当这个文件被直接运行时（python feishu_bot.py），执行 main()
# 当被 import 时（from feishu_bot import ...），不执行 main()
# ====================================================================
if __name__ == "__main__":
    main()
