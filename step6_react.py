"""
第六步 - 高级概念示例 1：ReAct 模式
====================================
ReAct = Reasoning + Acting（推理 + 行动）

核心思想：让 Agent 先思考再行动，形成循环

运行：python step6_react.py
"""

from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== 模拟工具 ==========

def search_web(query: str) -> str:
    """模拟网络搜索"""
    results = {
        "周杰伦 出生地": "周杰伦（Jay Chou），1979 年 1 月 18 日出生于台湾省新北市",
        "Python 创始人": "Guido van Rossum，荷兰程序员，1989 年圣诞节开始开发 Python",
        "特斯拉 CEO": "埃隆·马斯克（Elon Musk），1971 年 6 月 28 日出生于南非",
        "珠穆朗玛峰 高度": "8848.86 米（2020 年中尼联合测量）"
    }
    return results.get(query, f"搜索结果：关于'{query}'的信息（模拟数据）")

def calculator(expr: str) -> str:
    """计算器"""
    try:
        return str(eval(expr))
    except:
        return "计算错误"

def fact_check(statement: str) -> str:
    """事实核查"""
    return f"核查结果：'{statement}' - 需要更多来源验证（模拟）"

TOOLS = {
    "search_web": search_web,
    "calculator": calculator,
    "fact_check": fact_check
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索网络获取信息",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"]
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
                "properties": {"expr": {"type": "string"}},
                "required": ["expr"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fact_check",
            "description": "核查事实陈述的准确性",
            "parameters": {
                "type": "object",
                "properties": {"statement": {"type": "string"}},
                "required": ["statement"]
            }
        }
    }
]

# ========== ReAct Agent ==========

class ReActAgent:
    """
    ReAct 模式 Agent
    
    核心循环：
    思考 → 行动 → 观察 → 思考 → 行动 → ... → 回答
    """
    
    def __init__(self):
        self.system_prompt = """你是一个使用 ReAct 模式解决问题的 AI 助手。

解决问题时，请遵循以下步骤：
1. 思考（Thought）：分析当前情况，决定下一步做什么
2. 行动（Action）：调用合适的工具
3. 观察（Observation）：查看工具返回的结果
4. 重复以上步骤，直到有足够信息回答问题
5. 最终回答（Answer）：给出完整答案

请用以下格式输出思考过程：
Thought: [你的思考]
Action: [工具名]
Action Input: {"param": "value"}
Observation: [工具返回结果]
...
Answer: [最终答案]
"""
        self.messages = [{"role": "system", "content": self.system_prompt}]
    
    def solve(self, question: str, max_iterations: int = 5) -> str:
        """
        使用 ReAct 模式解决问题
        
        Args:
            question: 需要解决的问题
            max_iterations: 最大思考 - 行动循环次数
        """
        self.messages.append({"role": "user", "content": question})
        
        print(f"\n{'='*60}")
        print(f"问题：{question}")
        print(f"{'='*60}\n")
        
        for i in range(max_iterations):
            print(f"--- 第 {i+1} 轮思考 ---\n")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                temperature=0  # 低温度，更 deterministic
            )
            
            message = response.choices[0].message
            self.messages.append(message)
            
            # 检查是否需要调用工具
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🤔 思考：需要调用 {tool_name}")
                    print(f"🔧 行动：{tool_name}({tool_args})")
                    
                    # 执行工具
                    result = TOOLS[tool_name](**tool_args)
                    
                    print(f"👁️ 观察：{result}\n")
                    
                    # 返回结果给 LLM
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                # 没有工具调用，给出最终答案
                answer = message.content
                print(f"✅ 答案：{answer}\n")
                print(f"{'='*60}\n")
                return answer
        
        print("⚠️  达到最大迭代次数，返回当前最佳答案\n")
        return self.messages[-1].content if self.messages else "无法回答"


# ========== 测试 ==========

if __name__ == "__main__":
    agent = ReActAgent()
    
    # 测试 1：需要多步推理的问题
    print("\n【测试 1】需要搜索 + 计算的问题")
    agent.solve("周杰伦出生到现在多少年了？")
    
    # 测试 2：需要事实核查
    print("\n【测试 2】需要验证信息")
    agent2 = ReActAgent()
    agent2.solve("特斯拉的 CEO 是哪里人？")
    
    # 测试 3：复杂问题
    print("\n【测试 3】多步骤问题")
    agent3 = ReActAgent()
    agent3.solve("珠穆朗玛峰的高度除以 100 是多少？")
