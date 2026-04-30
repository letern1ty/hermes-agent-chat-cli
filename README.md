# 🤖 Hermes Agent Chat CLI

> 30 天从零构建你的第一个 AI Agent 系统 | 适合前端工程师转型 AI 开发

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/letern1ty/hermes-agent-chat-cli?style=social)](https://github.com/letern1ty/hermes-agent-chat-cli/stargazers)

---

## 🚀 5 分钟快速开始

```bash
# 1. 克隆项目
git clone https://github.com/letern1ty/hermes-agent-chat-cli.git
cd hermes-agent-chat-cli

# 2. 配置 API Key
cp docs/.env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY

# 3. 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 启动 Web 界面
python src/web_chat.py

# 5. 访问 http://localhost:8000
```

---

## ✨ 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| 🛠️ 工具调用 | 天气查询、计算器、时间查询 | ✅ |
| 💬 对话记忆 | 多轮对话，上下文理解 | ✅ |
| 🌐 Web 界面 | 响应式设计，支持 Markdown | ✅ |
| 📱 移动端适配 | 手机/平板完美显示 | ✅ |
| 🤖 模型切换 | 支持 Qwen / DeepSeek 双模型 | ✅ |
| 📬 飞书机器人 | 在飞书里跟 AI 对话 | ✅ |
| 📖 RAG 知识库 | 文档问答系统 | 📅 计划中 |

---

## 📁 项目结构

```
hermes-agent-chat-cli/
├── src/                          # 核心代码
│   ├── feishu_bot.py             # 飞书机器人（带大量学习注释）
│   └── web_chat.py               # Web 聊天服务器
│
├── scripts/                      # 启动/管理脚本
│   ├── start.sh                  # 一键启动（网页 + 自动同步）
│   ├── run_feishu.sh             # 飞书机器人启动
│   ├── auto-sync.sh              # 文件监听 + 自动 Git 推送
│   ├── sync.sh                   # 手动同步
│   ├── status.sh                 # 状态检查
│   ├── feishu_config.sh          # 飞书配置（App ID/Secret）
│   └── .gitkeep
│
├── web/                          # 前端文件
│   └── chat.html                 # 响应式聊天界面
│
├── docs/                         # 学习文档
│   ├── LEARNING_PATH.md          # 30 天学习计划
│   ├── DETAILED_GUIDE.md         # 详细实现指南
│   ├── STEP6_GUIDE.md            # 第 6 步（ReAct/规划/多 Agent）
│   ├── PYTHON_QUICKSTART.md      # Python 速成
│   ├── API_CONFIG.md             # API 配置指南
│   ├── WEB_IMPLEMENTATION_EXPLAINED.md  # Web 实现详解
│   ├── feishu_setup_guide.md     # 飞书机器人设置
│   └── .env.example              # API Key 配置模板
│
├── day01-05/                     # 第 1 周：基础入门
│   ├── README.md
│   ├── day01_agent_basic.py
│   ├── day1_practice.py
│   └── day1_test.py
│
├── day06-10/                     # 第 2 周：高级概念
│   ├── README.md
│   └── ...
│
├── day11-15/                     # 预留
├── day16-20/                     # 预留
├── legacy/                       # 旧版本代码（参考用）
├── .github/                      # Issue/PR 模板
│
├── .env                          # ⚠️ 本地配置，勿提交 Git
├── .gitignore
├── .env.example
├── requirements.txt
└── README.md
```

---

## 📅 学习路径

**30 天从零到实战：**

```
第 1 周：基础入门     →  day01-05/  (Day 1-5)
第 2 周：高级概念     →  day06-10/  (ReAct、规划、多 Agent)
第 3 周：RAG 知识库   →  day11-15/  (向量数据库)
第 4 周：实战项目     →  day16-20/  (代码审查 Agent)
第 5 周：集成部署     →  飞书机器人、云服务器部署
第 6 周：简历优化     →  项目整理、面试准备
```

📖 详细计划看 [docs/LEARNING_PATH.md](docs/LEARNING_PATH.md)

---

## 🤖 飞书机器人

在飞书 App 里跟你的 AI 助手对话：

```bash
# 启动服务
bash scripts/run_feishu.sh

# 启动公网隧道（需要 cloudflared）
cloudflared tunnel --url http://localhost:8655

# 配置回调地址到飞书开放平台
# 详见 docs/feishu_setup_guide.md
```

支持：天气查询、算数、个人信息查询、多轮对话记忆。

---

## 🛠️ 技术栈

| 分类 | 技术 |
|------|------|
| **后端** | Python 3.13 + http.server / FastAPI |
| **LLM** | DeepSeek Chat / 阿里云 Qwen |
| **前端** | HTML + CSS + JavaScript（原生） |
| **飞书集成** | 飞书开放平台 API + cloudflared 隧道 |

---

## 🔒 安全说明

- `.env` 和 `scripts/feishu_config.sh` 已在 `.gitignore` 中排除
- API Key 和 App Secret 永远不提交到 Git
- 如果不慎提交，用 `git filter-branch` 从历史中清除（参见 commit 记录）

---

## ⭐ Star 支持

如果这个项目对你有帮助，请给一个 **Star** ⭐️ 支持一下！

[![Star History Chart](https://api.star-history.com/svg?repos=letern1ty/hermes-agent-chat-cli&type=Date)](https://star-history.com/#letern1ty/hermes-agent-chat-cli&Date)
