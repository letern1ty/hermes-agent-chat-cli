# AI Agent 超详细学习指南（零基础版）

> 每一个步骤都解释清楚，不跳过任何细节

---

## 学习前准备

### 你需要知道的背景知识

**问题 1：什么是 LLM？**
```
LLM = Large Language Model（大语言模型）
简单理解：一个读过很多书的超级大脑

它能做什么：
✓ 理解人类语言
✓ 生成文本回复
✓ 回答问题
✓ 写代码
✓ 翻译

它不能做什么：
✗ 不能直接操作电脑（不能自己打开文件、运行程序）
✗ 不能获取实时信息（不知道今天的天气、新闻）
✗ 记忆有限（对话太长会忘记前面的内容）
```

**问题 2：什么是 Agent？**
```
Agent = LLM + 工具 + 记忆 + 规划

通俗理解：
LLM 像一个被关在房间里的天才
- 它很聪明，但手被绑住了
- 它不能自己查资料、不能自己运行代码

Agent 就是给这个天才：
- 一双手（工具）：可以查资料、运行代码、读写文件
- 一个笔记本（记忆）：可以记录之前做过的事
- 一个计划本（规划）：可以把大任务拆成小步骤

现在这个天才可以真正帮你做事了！
```

---

## 第一步：理解最核心的概念 —— 工具调用

### 1.1 为什么要用工具？

**场景**：你问 LLM "北京今天天气怎么样？"

**没有工具时**：
```
LLM 内心 OS：
"我只知道训练数据里的信息，不知道今天的天气
但我不能说我不知道，用户会失望
算了，编一个吧... 北京现在大概 25 度？"

结果：LLM 瞎编（术语叫"幻觉"）
```

**有工具时**：
```
LLM 内心 OS：
"我不知道今天的天气，但我可以用天气工具查一下"

过程：
1. LLM 说："我需要调用 weather 工具，参数是 city=北京"
2. 你的代码真正调用天气 API
3. 得到结果："25°C，晴"
4. 把结果告诉 LLM
5. LLM 回复："北京现在 25°C，晴天"

结果：准确信息
```

### 1.2 工具调用的完整流程（图解）

```
┌────────────────────────────────────────────────────────────┐
│ 第 1 步：用户提问                                            │
│ "北京天气怎么样？"                                          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ 第 2 步：LLM 分析                                            │
│ LLM 看到这个问题，心想：                                     │
│ "这个问题需要实时天气数据，我自己不知道                       │
│  但我有一个 weather 工具可以用                               │
│  我应该调用这个工具"                                        │
│                                                            │
│ LLM 返回（JSON 格式）：                                      │
│ {                                                          │
│   "tool_call": {                                           │
│     "name": "get_weather",                                 │
│     "arguments": {"city": "北京"}                           │
│   }                                                        │
│ }                                                          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ 第 3 步：你的代码执行工具                                     │
│ 你的代码看到 LLM 想调用工具，就真正执行：                     │
│                                                            │
│ result = get_weather(city="北京")                           │
│                                                            │
│ 这个函数内部调用天气 API，得到：                             │
│ result = "25°C, 晴"                                        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ 第 4 步：把结果告诉 LLM                                       │
│ 你的代码对 LLM 说：                                          │
│ "你刚才调用 get_weather(北京) 的结果是：25°C, 晴"            │
│                                                            │
│ 这个消息格式：                                              │
│ {                                                          │
│   "role": "tool",                                          │
│   "content": "25°C, 晴"                                    │
│ }                                                          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ 第 5 步：LLM 生成最终回复                                     │
│ LLM 看到工具返回的结果，心想：                               │
│ "好的，我知道北京天气了，可以回答用户了"                     │
│                                                            │
│ LLM 返回：                                                  │
│ "北京现在 25°C，晴天"                                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ 第 6 步：用户看到回复                                         │
│ "北京现在 25°C，晴天"                                       │
└────────────────────────────────────────────────────────────┘
```

### 1.3 关键理解点

**重点 1：LLM 不直接执行工具**
```
错误理解：LLM 调用工具 → 得到结果 → 返回答案
正确理解：LLM 说"我想调用工具" → 你的代码执行 → 告诉 LLM 结果 → LLM 返回答案

为什么？
- LLM 只是一个语言模型，它不能真正运行代码
- 它只能生成文本（包括"我想调用 XX 工具"这样的文本）
- 真正执行工具的是你的 Python 代码
```

**重点 2：工具调用是一个循环**
```
while True:
    1. 调用 LLM
    2. LLM 说"我要调用工具" → 执行工具 → 告诉 LLM 结果
    3. LLM 说"我要调用工具" → 执行工具 → 告诉 LLM 结果
    4. ...
    5. LLM 说"我有答案了" → 返回给用户 → 结束循环
```

**重点 3：工具需要预先定义**
```
在调用 LLM 之前，你要告诉它：
"你可以使用以下工具：
  1. get_weather(city) - 查询天气
  2. calculator(expr) - 计算数学表达式
  3. ..."

LLM 才知道它有哪些工具可以用，以及怎么调用。
```

---

## 第二步：逐行代码讲解

### 2.1 最简 Agent 代码（只有 30 行）

打开文件：`~/my-first-agent/agent.py`

我们逐行讲解核心部分：

```python
# ========== 第 1 部分：导入必要的库 ==========
from openai import OpenAI      # OpenAI 的 Python 客户端，用来调用 GPT
import os                      # 操作系统接口，用来读取环境变量
import json                    # JSON 处理，用来解析工具调用参数
from dotenv import load_dotenv # 加载.env 文件中的环境变量

load_dotenv()  # 读取.env 文件，这样 os.getenv() 才能拿到 API Key

# ========== 第 2 部分：初始化 LLM 客户端 ==========
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# 这行代码创建一个"连接器"，通过它可以和 GPT 对话
# api_key 是你的身份凭证，没有它 GPT 不理你

# ========== 第 3 部分：定义工具 ==========
def get_weather(city: str) -> str:
    """获取天气（这是一个普通 Python 函数）"""
    weather_data = {
        "北京": "25°C, 晴",
        "上海": "28°C, 多云",
    }
    return weather_data.get(city, "未知城市")

# 这个函数就是"工具"
# 当 LLM 说"我要查北京天气"时，你的代码就调用这个函数
# 然后把结果告诉 LLM

# ========== 第 4 部分：告诉 LLM 有哪些工具可用 ==========
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",           # 工具名字
            "description": "获取城市天气",     # 工具描述
            "parameters": {                   # 工具需要什么参数
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名"
                    }
                },
                "required": ["city"]  # city 是必填的
            }
        }
    }
]

# 这个列表告诉 LLM：
# "你可以用 get_weather 工具，它需要一个 city 参数"
# LLM 看到后，就知道什么时候调用这个工具，以及怎么调用

# ========== 第 5 部分：Agent 核心循环 ==========
def agent_chat(user_message: str) -> str:
    # 这是 Agent 的核心函数
    # 输入：用户说的话
    # 输出：Agent 的回复
    
    # 初始化对话历史
    messages = [{"role": "user", "content": user_message}]
    # messages 数组记录整个对话过程
    # 格式：[{"role": "user", "content": "你好"}, 
    #        {"role": "assistant", "content": "你好！有什么可以帮你？"},
    #        ...]
    
    while True:  # 循环开始
        # --- 第 1 步：调用 LLM ---
        response = client.chat.completions.create(
            model="gpt-4o",      # 使用 GPT-4o 模型
            messages=messages,   # 把对话历史发给它
            tools=TOOL_DEFINITIONS  # 告诉它有哪些工具可用
        )
        
        message = response.choices[0].message
        # message 是 LLM 的回复，可能有两种情况：
        # 1. 直接回答（message.content 有内容）
        # 2. 想调用工具（message.tool_calls 有内容）
        
        messages.append(message)
        # 把 LLM 的回复也加入对话历史
        
        # --- 第 2 步：检查 LLM 是否想调用工具 ---
        if message.tool_calls:
            # LLM 说："我想调用工具！"
            
            for tool_call in message.tool_calls:
                # 可能有多个工具调用，逐个处理
                
                tool_name = tool_call.function.name
                # 工具名字，比如 "get_weather"
                
                tool_args = json.loads(tool_call.function.arguments)
                # 工具参数，比如 {"city": "北京"}
                # 注意：arguments 是 JSON 字符串，需要解析
                
                print(f"调用工具：{tool_name}({tool_args})")
                
                # --- 第 3 步：真正执行工具 ---
                if tool_name == "get_weather":
                    result = get_weather(**tool_args)
                    # 相当于：get_weather(city="北京")
                    # **tool_args 是 Python 的"解包"语法
                    # {"city": "北京"} 变成 city="北京"
                
                print(f"工具结果：{result}")
                
                # --- 第 4 步：把结果告诉 LLM ---
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                # 这步很关键！
                # 告诉 LLM："你刚才调用的工具返回了这个结果"
                # LLM 看到结果后，就可以生成最终答案了
                
                # 然后循环继续，再次调用 LLM
                # 这次 LLM 看到工具结果，就可以回答用户了
                
        else:
            # LLM 没有调用工具，说明它有答案了
            
            return message.content
            # 返回最终答案给用户
            # 循环结束
```

### 2.2 运行流程示例

假设用户问："北京天气怎么样？"

**第 1 轮循环**：
```
输入给 LLM：
messages = [
  {"role": "user", "content": "北京天气怎么样？"}
]

LLM 思考：
"用户问北京天气，我不知道实时天气
 但我有 get_weather 工具可以用
 我应该调用这个工具"

LLM 返回：
{
  "tool_calls": [
    {
      "id": "call_123",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"北京\"}"
      }
    }
  ]
}

你的代码执行：
result = get_weather(city="北京")  →  "25°C, 晴"

告诉 LLM：
messages.append({
  "role": "tool",
  "tool_call_id": "call_123",
  "content": "25°C, 晴"
})
```

**第 2 轮循环**：
```
输入给 LLM：
messages = [
  {"role": "user", "content": "北京天气怎么样？"},
  {"role": "assistant", "tool_calls": [...]},
  {"role": "tool", "content": "25°C, 晴"}
]

LLM 思考：
"好的，工具告诉我北京 25°C 晴
 现在我可以回答用户了"

LLM 返回：
{
  "content": "北京现在 25°C，晴天"
}

你的代码：
没有 tool_calls，直接返回答案
循环结束
```

---

## 第三步：动手实践

### 3.1 运行你的第一个 Agent

```bash
# 1. 进入项目目录
cd ~/my-first-agent

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 运行测试（需要 API Key）
python agent.py --test
```

### 3.2 观察输出

你应该看到类似这样的输出：
```
=== Agent 测试 ===

[测试 1] 天气查询
用户：北京天气怎么样？

🔧 调用工具：get_weather({'city': '北京'})
📦 工具结果：25°C, 晴

🤖 Agent: 北京现在 25°C，晴天
```

### 3.3 理解每一行输出

| 输出 | 含义 | 对应代码 |
|------|------|----------|
| `🔧 调用工具` | LLM 决定调用工具 | `if message.tool_calls:` |
| `📦 工具结果` | 你的代码执行了工具 | `result = get_weather(...)` |
| `🤖 Agent: ...` | LLM 生成最终答案 | `return message.content` |

---

## 第四步：修改代码，加深理解

### 练习 1：添加一个新工具

目标：让 Agent 可以查询当前时间

**步骤 1**：在 `agent.py` 中找到 `TOOLS` 字典，添加：

```python
def get_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_time": get_time,  # 新增这一行
}
```

**步骤 2**：在 `TOOL_DEFINITIONS` 中添加：

```python
{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "获取当前时间",
        "parameters": {
            "type": "object",
            "properties": {}  # 不需要参数
        }
    }
}
```

**步骤 3**：运行测试
```bash
python agent.py
# 然后问："现在几点了？"
```

### 练习 2：修改工具的返回值

目标：让天气工具返回更详细的信息

找到 `get_weather` 函数，修改为：

```python
def get_weather(city: str) -> str:
    weather_data = {
        "北京": "25°C, 晴，湿度 40%, 东北风 2 级",
        "上海": "28°C, 多云，湿度 65%, 东南风 3 级",
        # ...
    }
    return weather_data.get(city, f"{city}的天气数据暂不可用")
```

运行测试，观察 Agent 的回答是否更详细。

### 练习 3：添加调试输出

在 `agent.chat()` 方法中，添加更多 print：

```python
def chat(self, user_message: str, verbose: bool = True):
    self.messages.append({"role": "user", "content": user_message})
    
    while True:
        print("\n=== 调用 LLM ===")
        print(f"发送的消息：{self.messages}")
        
        response = client.chat.completions.create(...)
        
        print(f"\nLLM 返回：{response.choices[0].message}")
        
        # ... 其余代码
```

这样你可以看到完整的对话历史，理解 LLM 是如何"思考"的。

---

## 第五步：理解对话历史（记忆）

### 5.1 为什么需要记忆？

**没有记忆时**：
```
用户：我叫小明
Agent: 好的，小明

用户：我记得我叫什么？
Agent: 抱歉，我不知道你叫什么

（因为每次对话都是新的，Agent 不记得之前的事）
```

**有记忆时**：
```
用户：我叫小明
Agent: 好的，小明

用户：我记得我叫什么？
Agent: 你叫小明

（因为对话历史被保存了，Agent 可以看到之前的对话）
```

### 5.2 记忆是如何实现的？

```python
class Agent:
    def __init__(self):
        self.messages = [
            {"role": "system", "content": "你是一个有用的助手"}
        ]
        # 这个列表就是"记忆"
        # 它保存了整个对话历史
    
    def chat(self, user_message: str):
        self.messages.append({"role": "user", "content": user_message})
        # 每次用户说话，都加入历史
        
        response = client.chat.completions.create(
            messages=self.messages,  # 把完整历史发给 LLM
            ...
        )
        
        self.messages.append(response.choices[0].message)
        # LLM 的回复也加入历史
        
        return response.choices[0].message.content
```

### 5.3 动手实验

运行交互模式：
```bash
python agent.py
```

然后测试：
```
👤 你：我叫小明
🤖 Agent: 好的，小明，有什么可以帮你？

👤 你：我喜欢吃苹果
🤖 Agent: 好的，我记住了你喜欢吃苹果

👤 你：我叫什么？喜欢吃什么？
🤖 Agent: 你叫小明，喜欢吃苹果
```

然后清空历史：
```
👤 你：clear
🗑️ 对话历史已清空

👤 你：我叫什么？
🤖 Agent: 抱歉，我不知道你叫什么
```

---

## 第六步：高级概念（等你完成前五步再学）

完成前五步后，你已经理解了：
- ✓ 工具调用的原理
- ✓ Agent 核心循环
- ✓ 对话历史（记忆）
- ✓ 如何添加新工具

这时再学习：
- ReAct 模式（多步推理）
- 规划模式（任务拆解）
- 多 Agent 协作

会更容易理解。

---

## 学习检查清单

完成每一步后，问自己：

**第一步后**：
- [ ] 我能解释为什么需要工具调用吗？
- [ ] 我能画出工具调用的流程图吗？

**第二步后**：
- [ ] 我能逐行解释 agent.py 的代码吗？
- [ ] 我知道 messages 数组的作用吗？

**第三步后**：
- [ ] 我能成功运行 agent.py 吗？
- [ ] 我能看懂输出中的每一行吗？

**第四步后**：
- [ ] 我能自己添加一个新工具吗？
- [ ] 我知道 tool_definitions 的作用吗？

**第五步后**：
- [ ] 我理解为什么需要对话历史吗？
- [ ] 我能演示"清空历史"的效果吗？

---

## 下一步

完成以上步骤后：

1. **如果还有疑问**：告诉我具体哪里不理解，我详细解释
2. **如果都理解了**：开始学习第六步（高级概念）
3. **如果想实践**：选择一个实战项目（代码审查 Agent、测试 Agent 等）

---

现在，从第一步开始，一步一步来。有任何问题随时问我！
