# 🤖 我的第一个 AI Agent

恭喜你！项目已经搭建好了。下面是快速开始指南。

---

## 📁 项目结构

```
~/my-first-agent/
├── agent.py          # 命令行版 Agent（直接运行）
├── server.py         # Web 服务器（带界面）
├── index.html        # Web 界面
├── .env              # API Key 配置文件（需要编辑）
└── README.md         # 本文件
```

---

## ⚙️ 第一步：配置 API Key

### 选项 A：使用 OpenAI（推荐）

1. 访问 https://platform.openai.com/api-keys
2. 登录/注册账号
3. 点击 "Create new secret key"
4. 复制 API Key（以 `sk-` 开头）
5. 编辑 `.env` 文件：

```bash
# 打开文件
code ~/.env  # 或你喜欢的编辑器

# 修改这一行：
OPENAI_API_KEY=sk-你的真实 API Key
```

### 选项 B：使用智谱 AI（更便宜）

1. 访问 https://open.bigmodel.cn/
2. 注册账号并创建 API Key
3. 编辑 `agent.py`，把 `OpenAI` 改成 `ZhipuAI`（需要额外安装 `zhipuai` 库）

---

## 🚀 运行方式

### 方式 1：命令行版（简单）

```bash
cd ~/my-first-agent
source venv/bin/activate
python agent.py
```

**测试模式**：
```bash
python agent.py --test
```

**可用命令**：
- `quit` - 退出
- `clear` - 清空对话历史
- `save` - 保存对话到文件

### 方式 2：Web 版（推荐）

```bash
cd ~/my-first-agent
source venv/bin/activate
python server.py
```

然后打开浏览器访问：**http://localhost:8000**

API 文档：**http://localhost:8000/docs**

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

然后在 `TOOL_DEFINITIONS` 中添加工具定义（告诉 LLM 这个工具的用法）。

---

## 📚 学习下一步

完成这个练习后，你可以：

1. **阅读完整学习文档**：`~/agent-learning-guide.md`
2. **理解核心原理**：看 `agent.py` 中的 `Agent.chat()` 方法
3. **添加更多工具**：比如文件读写、网络搜索
4. **学习 Hermes Agent**：你已经在用的框架，源码在 `~/.hermes/hermes-agent/`

---

## ❓ 常见问题

### Q: 没有 API Key 能用吗？
A: 不行，需要至少一个 LLM 提供商的 API Key。新用户通常有免费额度。

### Q: 费用多少？
A: GPT-4o 约 $0.01/1K tokens，学习阶段每天 $1-2 足够。

### Q: 报错了怎么办？
A: 
1. 检查 `.env` 文件中 API Key 是否正确
2. 确保虚拟环境已激活：`source venv/bin/activate`
3. 运行 `python agent.py --test` 看详细错误

---

## 🎉 开始吧！

```bash
cd ~/my-first-agent
source venv/bin/activate

# 先测试（需要 API Key）
python agent.py --test

# 或者启动 Web 服务器
python server.py
```

祝你学习愉快！有问题随时问。
