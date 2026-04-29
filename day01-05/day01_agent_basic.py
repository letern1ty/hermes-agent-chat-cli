"""
Day 1: 第一个 AI Agent
====================
学习目标：理解工具调用的核心原理

核心概念：
- LLM 不能直接获取实时信息（天气、时间等）
- 工具调用 = LLM 决定调用什么工具 + 你的代码执行工具
- 流程：用户问 → LLM 分析 → 调用工具 → 返回结果 → LLM 回复

运行：
    python day01_agent_basic.py          # 交互模式
    python day01_agent_basic.py --test   # 测试模式

试试问：
    - 北京天气怎么样？
    - 帮我算一下 123 * 456
    - 现在几点了？
"""

from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# ========== 第 1 步：加载配置 ==========\nload_dotenv()

# 初始化客户端（使用阿里云 DashScope API）
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" if os.getenv("DASHSCOPE_API_KEY") else None

if not api_key:
    print("❌ 错误：没有找到 API Key")
    print("请在 .env 文件中配置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY")
    exit(1)

client = OpenAI(api_key=api_key, base_url=base_url)

# ========== 第 2 步：定义工具 ==========\n# 工具就是普通的 Python 函数，关键是告诉 LLM 怎么用

def get_weather(city: str) -> str:
    """
    获取指定城市的天气
    
    Args:
        city: 城市名，如"北京"、"上海"
    
    Returns:
        天气描述字符串
    """
    weather_data = {
        "北京": "25°C, 晴",
        "上海": "28°C, 多云",
        "深圳": "32°C, 小雨",
        "广州": "30°C, 阴",
        "杭州": "26°C, 小雨",
        "纽约": "18°C, 阴",
        "旧金山": "20°C, 晴"
    }
    return weather_data.get(city, f"⚠️ {city}的天气数据暂不可用")


def calculator(expression: str) -> str:
    """
    计算数学表达式
    
    Args:
        expression: 数学表达式，如"2+2"、"100*5"
    
    Returns:
        计算结果字符串
    """
    try:
        # 安全验证：只允许数字和基本运算符
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "❌ 错误：只允许数字和基本运算符 (+-*/)"
        
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"❌ 计算错误：{e}"


def get_time() -> str:
    """
    获取当前时间
    
    Returns:
        格式化时间字符串
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ========== 第 3 步：注册工具 ==========\n# 工具字典：名字 → 函数
TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_time": get_time,
}


# ========== 第 4 步：定义工具描述 ==========\n# 告诉 LLM 有哪些工具可用，以及怎么用（参数、描述）
# 这是关键！LLM 靠这个决定调用什么工具

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、深圳"
                    }
                },
                "required": ["city"]  # 必须提供的参数
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式的结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如：2+2、100*5、(3+4)*2"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {}  # 不需要参数
            }
        }
    }
]


# ========== 第 5 步：创建 Agent 类 ==========\nclass Agent:
    """
    简单的 AI Agent
    
    核心流程：
    1. 接收用户消息
    2. 调用 LLM（带上工具定义）
    3. LLM 决定是否需要调用工具
    4. 执行工具，返回结果给 LLM
    5. LLM 生成最终回复
    """
    
    def __init__(self):
        # 对话历史，从系统消息开始
        self.messages = [{
            "role": "system",
            "content": "你是一个有用的 AI 助手，可以使用工具来帮助用户。"
        }]
    
    def chat(self, user_message: str, verbose: bool = True) -> str:
        """
        与 Agent 对话
        
        Args:
            user_message: 用户输入的消息
            verbose: 是否打印详细日志（调试用）
        
        Returns:
            Agent 的回复
        """
        # 添加用户消息到历史
        self.messages.append({"role": "user", "content": user_message})
        
        # 循环：LLM 可能多次调用工具
        while True:
            # 1️⃣ 调用 LLM
            response = client.chat.completions.create(
                model="qwen3.5-plus",  # 使用阿里云 Qwen 模型
                messages=self.messages,
                tools=TOOL_DEFINITIONS
            )
            
            message = response.choices[0].message
            self.messages.append(message)
            
            # 2️⃣ 检查是否需要调用工具
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"\n🔧 调用工具：{tool_name}({tool_args})")
                    
                    # 3️⃣ 执行工具
                    if tool_name in TOOLS:
                        result = TOOLS[tool_name](**tool_args)
                    else:
                        result = f"❌ 错误：未知工具 {tool_name}"
                    
                    if verbose:
                        print(f"📦 工具结果：{result}")
                    
                    # 4️⃣ 把结果返回给 LLM
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                # 5️⃣ 没有工具调用，返回最终答案
                return message.content


# ========== 第 6 步：交互式命令行 ==========\ndef interactive_mode():
    """交互式对话模式"""
    print("=" * 50)
    print("🤖  Day 1: 我的第一个 AI Agent")
    print("=" * 50)
    print("可用工具：天气查询 | 计算器 | 时间查询")
    print("示例问题：")
    print("  - 北京天气怎么样？")
    print("  - 帮我算一下 123 * 456")
    print("  - 现在几点了？")
    print("-" * 50)
    print("输入 'quit' 退出，'clear' 清空历史")
    print("=" * 50)
    
    agent = Agent()
    
    while True:
        try:
            user_input = input("\n👤 你：").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("👋 再见！")
                break
            
            if user_input.lower() == 'clear':
                agent.messages = [agent.messages[0]]  # 保留系统消息
                print("🗑️  对话历史已清空")
                continue
            
            # 获取 Agent 回复
            response = agent.chat(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")


# ========== 第 7 步：测试模式 ==========\ndef run_tests():
    """运行内置测试"""
    print("=" * 50)
    print("🧪  Day 1: 运行测试")
    print("=" * 50)
    
    agent = Agent()
    
    # 测试 1：天气查询
    print("\n[测试 1] 天气查询")
    print("👤 用户：北京天气怎么样？")
    response = agent.chat("北京天气怎么样？", verbose=True)
    print(f"🤖 Agent: {response}")
    
    # 测试 2：计算器
    print("\n" + "=" * 50)
    print("[测试 2] 计算器")
    print("👤 用户：帮我算一下 123 * 456")
    response = agent.chat("帮我算一下 123 * 456", verbose=True)
    print(f"🤖 Agent: {response}")
    
    # 测试 3：时间查询
    print("\n" + "=" * 50)
    print("[测试 3] 时间查询")
    print("👤 用户：现在几点了？")
    response = agent.chat("现在几点了？", verbose=True)
    print(f"🤖 Agent: {response}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("=" * 50)


# ========== 主程序 ==========\nif __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    else:
        interactive_mode()
