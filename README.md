# 🤖 Hermes Agent Chat CLI

> 我的第一个 AI Agent 项目 - 学习 AI Agent 开发的实战项目

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📚 项目背景

这是一个用于学习 AI Agent 开发的实战项目，基于阿里云 DashScope API（通义千问）构建。

**学习目标**：从零基础开始，理解并实现 AI Agent 的核心功能：
- ✅ 工具调用（Function Calling）
- ✅ 对话记忆（Conversation Memory）
- ✅ ReAct 模式（推理 + 行动）
- ✅ 规划模式（Plan-and-Execute）
- ✅ 多 Agent 协作

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/letern1ty/hermes-agent-chat-cli.git
cd hermes-agent-chat-cli
```

### 2. 配置 API Key

编辑 `.env` 文件，添加你的阿里云 DashScope API Key：

```bash
DASHSCOPE_API_KEY=your_api_key_here
```

获取 API Key：https://dashscope.console.aliyun.com/apiKey

### 3. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 4. 运行

**命令行版**：
```bash
python agent.py
```

**Web 版**：
```bash
python server.py
# 访问 http://localhost:8000
```

---

## 📁 项目结构

```
hermes-agent-chat-cli/
├── agent.py              # 命令行版 Agent
├── server.py             # Web 服务器
├── index.html            # Web 界面
├── web_chat.py           # 新版 Web 聊天（支持模型选择）
├── step6_react.py        # ReAct 模式示例
├── step6_planning.py     # 规划模式示例
├── step6_multi_agent.py  # 多 Agent 协作示例
├── .env                  # 环境变量（API Key）
└── README.md             # 本文件
```

---

## 🧪 测试示例

试试问 Agent 这些问题：

```
1. 北京天气怎么样？
2. 帮我算一下 123 * 456
3. 现在几点了？
4. 我叫小明，记住我的名字
5. 我记得我叫什么？
```

---

## 📅 学习计划

| 周次 | 主题 | 内容 |
|------|------|------|
| 第 1 周 | 基础入门 | 环境搭建、工具调用、对话记忆 |
| 第 2 周 | 高级概念 | ReAct、规划模式、多 Agent |
| 第 3 周 | RAG 与知识库 | 向量数据库、文档检索 |
| 第 4 周 | 实战项目 | 前端代码审查 Agent |

---

## 🔧 添加新工具

编辑 `agent.py`，在 `TOOLS` 字典中添加：

```python
def random_number(min: int, max: int) -> str:
    """生成随机数"""
    import random
    return str(random.randint(min, max))

TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_time": get_time,
    "random_number": random_number,  # 新增
}
```

---

## 📝 学习资源

- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [LangChain 文档](https://python.langchain.com/)
- [Hermes Agent 源码](~/.hermes/hermes-agent/)

---

## 🎯 下一步

- [ ] 完成 Web 聊天界面（支持模型选择）
- [ ] 接入飞书机器人
- [ ] 实现 RAG 知识库
- [ ] 构建前端代码审查 Agent

---

## 📄 License

MIT License
