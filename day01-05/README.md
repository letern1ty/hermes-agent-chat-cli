# 第一周：基础入门（Day 1-5）

> 从零开始构建你的第一个 AI Agent

---

## 📅 本周目标

完成本周学习后，你将能够：

- ✅ 理解 LLM 和 Agent 的核心区别
- ✅ 实现工具调用（Function Calling）
- ✅ 构建对话记忆系统
- ✅ 创建 Web 聊天界面
- ✅ 添加自定义工具

---

## 📁 文件说明

| 文件 | 说明 | 运行方式 |
|------|------|----------|
| `day01_agent_basic.py` | 第一个 Agent（工具调用） | `python day01_agent_basic.py` |
| `day02_memory.py` | 对话记忆系统 | （待创建） |
| `day03_web_server.py` | Web 服务器 | （待创建） |
| `day04_tools.py` | 自定义工具 | （待创建） |
| `day05_optimization.py` | 错误处理与优化 | （待创建） |

---

## 🚀 Day 1: 第一个 AI Agent

### 运行

```bash
cd day01-05

# 交互模式
python day01_agent_basic.py

# 测试模式
python day01_agent_basic.py --test
```

### 示例对话

```
👤 你：北京天气怎么样？
🤖 Agent: 北京现在 25°C，晴天。

👤 你：帮我算一下 123 * 456
🤖 Agent: 123 * 456 = 56088

👤 你：现在几点了？
🤖 Agent: 现在是 2026-04-29 11:30:00
```

### 核心原理

```
用户提问 → LLM 分析 → 决定调用工具 → 执行工具 → 返回结果 → LLM 生成回复
```

### 关键代码

```python
# 1. 定义工具
def get_weather(city: str) -> str:
    return f"{city}的天气..."

# 2. 告诉 LLM 有哪些工具
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取城市天气",
            "parameters": {...}
        }
    }
]

# 3. 调用 LLM
response = client.chat.completions.create(
    model="qwen3.5-plus",
    messages=messages,
    tools=TOOL_DEFINITIONS
)

# 4. 执行工具
if message.tool_calls:
    result = get_weather(city="北京")
```

---

## 📝 学习任务

### Day 1 任务清单

- [ ] 阅读 `day01_agent_basic.py` 代码注释
- [ ] 运行测试模式，观察工具调用过程
- [ ] 尝试添加一个新工具（如：随机数生成）
- [ ] 向别人解释工具调用的流程

### 扩展练习

1. **添加随机数工具**
   ```python
   def random_number(min: int, max: int) -> str:
       import random
       return str(random.randint(min, max))
   ```

2. **添加日期计算工具**
   ```python
   def days_between(date1: str, date2: str) -> str:
       # 计算两个日期之间的天数
       ...
   ```

---

## 💡 常见问题

### Q: 为什么需要工具调用？

A: LLM 本身无法获取实时信息（天气、时间、新闻等），也无法执行操作（文件读写、API 调用等）。工具调用让 LLM 能够"使用"你的代码来扩展能力。

### Q: 工具定义中的 `parameters` 有什么用？

A: 告诉 LLM 这个工具需要什么参数、参数类型、是否必填。LLM 根据这个信息决定如何调用工具。

### Q: 如果工具调用失败了怎么办？

A: 返回错误信息给 LLM，它会尝试用其他方式回答，或者告诉用户出了问题。

---

## 🎯 下一步

完成 Day 1 后，继续：

1. **Day 2**: 添加对话记忆，让 Agent 记住上下文
2. **Day 3**: 创建 Web 界面，浏览器访问
3. **Day 4-5**: 扩展工具、优化错误处理

---

## 📚 相关资源

- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [本项目 GitHub](https://github.com/letern1ty/hermes-agent-chat-cli)
