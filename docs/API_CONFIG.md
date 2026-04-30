# API 配置指南

> 支持多模型切换：阿里云 Qwen 系列 + DeepSeek 系列

---

## 📋 支持的模型

| 提供商 | 模型 | 说明 | 价格 |
|--------|------|------|------|
| **阿里云** | qwen3.5-plus | Qwen3.5 增强版 | ¥0.004/1K tokens |
| **阿里云** | qwen-plus | 平衡性能和成本 | ¥0.002/1K tokens |
| **阿里云** | qwen-max | 最强性能 | ¥0.02/1K tokens |
| **阿里云** | qwen-turbo | 最快响应 | ¥0.001/1K tokens |
| **DeepSeek** | deepseek-chat | DeepSeek V3 | ¥0.002/1K tokens |
| **DeepSeek** | deepseek-reasoner | DeepSeek R1（推理） | ¥0.004/1K tokens |

---

## 🔑 获取 API Key

### 阿里云 DashScope

1. 访问：https://dashscope.console.aliyun.com/apiKey
2. 登录/注册阿里云账号
3. 点击"创建新的 API Key"
4. 复制 Key（以 `sk-` 开头）

**免费额度**：新用户注册赠送约 100 万 tokens

---

### DeepSeek

1. 访问：https://platform.deepseek.com/api_keys
2. 登录/注册 DeepSeek 账号
3. 点击"创建 API Key"
4. 复制 Key（以 `sk-` 开头）

**免费额度**：新用户注册赠送约 100 万 tokens

---

## ⚙️ 配置步骤

### 1. 复制配置文件

```bash
cd ~/my-first-agent
cp .env.example .env
```

### 2. 编辑 .env 文件

```bash
# 用你喜欢的编辑器打开
code .env  # VS Code
# 或
nano .env  # 终端编辑器
```

### 3. 填入 API Key

```bash
# 阿里云（必填，至少配置一个）
DASHSCOPE_API_KEY=sk-your-dashscope-key-here

# DeepSeek（可选，如需使用 DeepSeek 模型）
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

### 4. 保存并重启服务

```bash
# 如果服务正在运行，先停止（Ctrl+C）
# 然后重启
python web_chat.py
```

---

## 🌐 切换模型

### 方式 1：Web 界面（推荐）

1. 访问 http://localhost:8000
2. 点击右上角的模型选择器
3. 选择想要的模型
4. 发送消息即生效

**效果**：
```
选择 "Qwen3.5-Plus" → 用阿里云 API
选择 "DeepSeek V3"   → 用 DeepSeek API
```

### 方式 2：API 调用

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "message": "你好",
    "model": "deepseek-chat"
  }'
```

**可用模型 ID**：
- `qwen3.5-plus`
- `qwen-plus`
- `qwen-max`
- `qwen-turbo`
- `deepseek-chat`
- `deepseek-reasoner`

---

## 🎯 模型选择建议

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 日常对话 | qwen-plus | 性价比高 |
| 复杂任务 | qwen-max / deepseek-chat | 性能最强 |
| 代码生成 | deepseek-chat | 代码能力强 |
| 数学推理 | deepseek-reasoner | 推理优化 |
| 快速响应 | qwen-turbo | 延迟最低 |
| 省钱 | qwen-turbo | 最便宜 |

---

## ❓ 常见问题

### Q: 可以不配置 DeepSeek 吗？

A: 可以！只配置阿里云也能用，DeepSeek 是可选的。

### Q: 两个都配置了，默认用哪个？

A: 默认用阿里云的 `qwen3.5-plus`，可以在 Web 界面切换。

### Q: 切换模型后，对话历史会保留吗？

A: 会保留！会话历史是按 `session_id` 存储的，和模型无关。

### Q: 费用怎么算？

A: 分别计算：
- 阿里云的调用从阿里云账户扣费
- DeepSeek 的调用从 DeepSeek 账户扣费

### Q: 可以临时切换吗？

A: 可以！每次发消息都可以选不同模型，互不影响。

---

## 📊 监控用量

### 阿里云

访问：https://dashscope.console.aliyun.com/usage

### DeepSeek

访问：https://platform.deepseek.com/billing

---

## 🔒 安全提示

1. **不要把 `.env` 文件提交到 GitHub**
   - 项目已配置 `.gitignore`，自动忽略 `.env`
   - 只提交 `.env.example`（不含真实 Key）

2. **定期轮换 API Key**
   - 建议每 3 个月更换一次

3. **监控异常用量**
   - 设置用量告警
   - 发现异常及时冻结 Key

---

## 🆘 遇到问题？

### 错误：API Key 无效

```
检查 .env 文件：
1. Key 是否复制完整（没有多余空格）
2. 环境变量名是否正确
3. 服务是否重启
```

### 错误：余额不足

```
解决方案：
1. 充值对应平台账户
2. 或切换到另一个有余额的模型
```

### 错误：服务不可用

```
检查：
1. 网络是否正常
2. API 服务是否维护中
3. 尝试切换其他模型
```

---

有问题？提 Issue：https://github.com/letern1ty/hermes-agent-chat-cli/issues
