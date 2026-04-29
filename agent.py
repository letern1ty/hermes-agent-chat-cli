"""
我的第一个 AI Agent
=================
功能：工具调用 + 对话记忆

运行：python agent.py
"""

from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化客户端（使用阿里云 Qwen API）
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" if os.getenv("DASHSCOPE_API_KEY") else None

client = OpenAI(api_key=api_key, base_url=base_url)

# ========== 定义工具 ==========

def get_weather(city: str) -> str:
    """获取天气（模拟数据）"""
    weather_data = {
        "北京": "25°C, 晴",
        "上海": "28°C, 多云",
        "深圳": "32°C, 小雨",
        "广州": "30°C, 阴",
        "杭州": "26°C, 小雨",
        "纽约": "18°C, 阴",
        "旧金山": "20°C, 晴"
    }
    return weather_data.get(city, f"{city}的天气数据暂不可用")

def calculator(expression: str) -> str:
    """计算器"""
    try:
        # 只允许安全的数学运算
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "错误：只允许数字和基本运算符 (+-*/)"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误：{e}"

def get_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 工具注册表
TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_time": get_time
}

# 工具定义（告诉 LLM 有哪些工具可用）
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如北京、上海"}
                },
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
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 2+2 或 100*5"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "获取当前时间",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# ========== Agent 核心类 ==========

class Agent:
    def __init__(self, system_prompt="你是一个有用的 AI 助手，可以使用工具来帮助用户。"):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.tool_definitions = TOOL_DEFINITIONS
        self.tools = TOOLS
    
    def chat(self, user_message: str, verbose: bool = True) -> str:
        """
        与 Agent 对话
        
        Args:
            user_message: 用户消息
            verbose: 是否打印详细日志
        
        Returns:
            Agent 的回复
        """
        self.messages.append({"role": "user", "content": user_message})
        
        while True:
            # 1. 调用 LLM
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=self.messages,
                tools=self.tool_definitions
            )
            
            message = response.choices[0].message
            self.messages.append(message)
            
            # 2. 检查是否需要调用工具
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"\n🔧 调用工具：{tool_name}({tool_args})")
                    
                    # 3. 执行工具
                    if tool_name in self.tools:
                        result = self.tools[tool_name](**tool_args)
                    else:
                        result = f"错误：未知工具 {tool_name}"
                    
                    if verbose:
                        print(f"📦 工具结果：{result}")
                    
                    # 4. 把结果返回给 LLM
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                # 5. 没有工具调用，返回最终答案
                return message.content
    
    def get_history(self) -> list:
        """获取对话历史"""
        return self.messages
    
    def clear_history(self):
        """清空对话历史"""
        self.messages = [{"role": "system", "content": "你是一个有用的 AI 助手，可以使用工具来帮助用户。"}]
    
    def save_history(self, filepath: str = "chat_history.json"):
        """保存对话历史到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)
        print(f"💾 对话历史已保存到 {filepath}")
    
    def load_history(self, filepath: str = "chat_history.json"):
        """从文件加载对话历史"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.messages = json.load(f)
            print(f"📂 已加载对话历史：{filepath}")
        else:
            print(f"⚠️  文件不存在：{filepath}")


# ========== 交互式命令行界面 ==========

def interactive_mode():
    """交互式对话模式"""
    print("=" * 50)
    print("🤖  我的 AI Agent")
    print("=" * 50)
    print("可用工具：天气查询、计算器、时间查询")
    print("输入 'quit' 退出，'clear' 清空历史，'save' 保存历史")
    print("=" * 50)
    
    agent = Agent()
    
    # 加载之前的历史（如果有）
    if os.path.exists("chat_history.json"):
        agent.load_history()
    
    while True:
        try:
            user_input = input("\n👤 你：").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("👋 再见！")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("🗑️  对话历史已清空")
                continue
            
            if user_input.lower() == 'save':
                agent.save_history()
                continue
            
            # 获取 Agent 回复
            response = agent.chat(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")


# ========== 测试模式 ==========

def run_tests():
    """运行内置测试"""
    print("=" * 50)
    print("🧪  运行测试")
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
    
    # 测试 4：多轮对话（记忆测试）
    print("\n" + "=" * 50)
    print("[测试 4] 多轮对话（记忆测试）")
    agent.clear_history()
    print("👤 用户：我叫小明")
    response = agent.chat("我叫小明", verbose=False)
    print(f"🤖 Agent: {response}")
    
    print("👤 用户：我记得我叫什么？")
    response = agent.chat("我记得我叫什么？", verbose=False)
    print(f"🤖 Agent: {response}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")
    print("=" * 50)


# ========== 主程序 ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    else:
        interactive_mode()
