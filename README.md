# 🤖 Hermes Agent Chat CLI

> 30 天从零构建你的第一个 AI Agent 系统 | 适合前端工程师转型 AI 开发

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/letern1ty/hermes-agent-chat-cli?style=social)](https://github.com/letern1ty/hermes-agent-chat-cli/stargazers)
[![Learning Path](https://img.shields.io/badge/学习路径 -30 天-orange)](LEARNING_PATH.md)

---

## 🚀 5 分钟快速开始

```bash
# 1. 克隆项目
git clone https://github.com/letern1ty/hermes-agent-chat-cli.git
cd hermes-agent-chat-cli

# 2. 配置 API Key（阿里云 DashScope，新用户有免费额度）
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY

# 3. 安装依赖
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 4. 启动 Web 界面
python web_chat.py

# 5. 访问 http://localhost:8000
```

**就这么简单！** 现在你可以和 AI 对话了 🎉

---

## ✨ 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| 🛠️ 工具调用 | 天气查询、计算器、时间查询 | ✅ 完成 |
| 💬 对话记忆 | 多轮对话，上下文理解 | ✅ 完成 |
| 🌐 Web 界面 | 响应式设计，支持 Markdown | ✅ 完成 |
| 📱 移动端适配 | 手机/平板完美显示 | ✅ 完成 |
| 🤖 模型切换 | 支持 Qwen 系列模型 | ✅ 完成 |
| 📚 学习计划 | 30 天从入门到实战 | ✅ 完成 |
| 📬 飞书机器人 | 在飞书里对话 | 🚧 开发中 |
| 📖 RAG 知识库 | 文档问答系统 | 📅 计划中 |

---

## 📅 30 天学习路径

完成这个项目，你将掌握：

```
第 1 周：基础入门
├─ Day 1: 第一个 AI Agent（工具调用）
├─ Day 2: 对话记忆系统
├─ Day 3: Web 服务器 + 前端界面
├─ Day 4: 自定义工具
└─ Day 5: 错误处理与优化

第 2 周：高级概念
├─ Day 6: ReAct 模式（推理 + 行动）
├─ Day 7: 规划模式（Plan-and-Execute）
├─ Day 8: 多 Agent 协作
├─ Day 9: 模式对比
└─ Day 10: Hermes 源码分析

第 3 周：RAG 与知识库
├─ Day 11-15: 向量数据库、文档检索、问答系统

第 4 周：实战项目
├─ Day 16-20: 前端代码审查 Agent

第 5 周：集成部署
├─ Day 21-25: 飞书机器人、云服务器部署

第 6 周：简历优化
├─ Day 26-30: 项目整理、面试准备
```

📖 **详细计划**：[LEARNING_PATH.md](LEARNING_PATH.md)

---

## 🎯 适合谁学

- ✅ **前端工程师**：想转型 AI 应用开发
- ✅ **Python 零基础**：有编程基础即可
- ✅ **想打造作品集**：面试时可展示
- ✅ **想接私活**：AI Agent 开发需求旺盛

**不适合**：
- ❌ 完全零基础（至少学过一门编程语言）
- ❌ 只想调 API 不想学原理

---

## 📁 项目结构

```
hermes-agent-chat-cli/
├── 📖 LEARNING_PATH.md       # 30 天学习计划（从这里开始）
├── 📦 requirements.txt        # Python 依赖
├── ⚙️ .env.example           # API Key 配置模板
│
├── 📂 day01-05/              # 第 1 周：基础入门
│   ├── README.md
│   └── day01_agent_basic.py  # Day 1 代码
│
├── 📂 day06-10/              # 第 2 周：高级概念
│   └── README.md
│
├── 📂 web/                   # Web 界面
│   └── chat.html             # 响应式聊天界面
│
├── 📂 integrations/          # 第三方集成
│   └── feishu_bot.py         # 飞书机器人（开发中）
│
└── 📂 legacy/                # 旧版本代码（参考用）
```

---

## 💡 学完你能做什么

### 技术能力
- ✅ 理解 LLM 和 Agent 的核心区别
- ✅ 实现工具调用（Function Calling）
- ✅ 构建 RAG 知识库系统
- ✅ 部署 AI 应用到云端

### 职业发展
- 📝 简历增加一个完整的 AI 项目
- 💼 面试 AI 应用工程师岗位
- 💰 接 AI Agent 开发私活（市场价 5k-20k/项目）

---

## 🎬 效果演示

### Web 界面
访问 http://localhost:8000 即可看到：

- 🎨 渐变紫色主题
- 💬 气泡式对话
- 📝 Markdown 渲染（代码高亮、表格、列表）
- 📱 移动端完美适配

### 示例对话

```
👤 你：北京天气怎么样？
🤖 Agent: 北京现在 25°C，晴天。

👤 你：帮我算一下 123 * 456
🤖 Agent: 123 × 456 = 56088

👤 你：用 Python 写一个快速排序
🤖 Agent: 
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
```

---

## 🛠️ 技术栈

| 分类 | 技术 |
|------|------|
| **后端** | Python 3.13 + FastAPI |
| **LLM** | 阿里云 DashScope（Qwen 系列） |
| **前端** | HTML + CSS + JavaScript（原生） |
| **Markdown** | marked.js + highlight.js |
| **部署** | 待定（Docker/云服务器） |

**为什么不用 React/Vue？**
- 学习曲线低，前端工程师一看就懂
- 零构建，直接打开 HTML 就能用
- 专注 AI 逻辑，不是前端技术

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 你可以贡献：
- 📝 完善学习计划
- 🐛 修复 Bug
- ✨ 添加新功能
- 📖 改进文档

### 开发流程：
```bash
# 1. Fork 项目
# 2. 创建分支
git checkout -b feature/your-feature

# 3. 提交代码
git commit -m "feat: 添加 xxx 功能"

# 4. 推送并创建 PR
git push origin feature/your-feature
```

---

## 📬 联系我

- 📧 Email: [你的邮箱]
- 💬 微信：[你的微信]
- 📝 博客：[你的博客]
- 💼 掘金：[你的掘金主页]

**加我微信备注 "AI Agent 学习"，拉你进学习交流群！**

---

## 📄 License

MIT License © 2026 [letern1ty](https://github.com/letern1ty)

---

## 🌟 如果这个项目对你有帮助

请给一个 **Star** ⭐️ 支持一下！

你的 Star 是我持续更新的动力 🚀

[![Star History Chart](https://api.star-history.com/svg?repos=letern1ty/hermes-agent-chat-cli&type=Date)](https://star-history.com/#letern1ty/hermes-agent-chat-cli&Date)
