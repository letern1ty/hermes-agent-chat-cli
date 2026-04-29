# 🤖 飞书机器人配置指南

本文档教你如何把 Hermes AI Agent 接入飞书，实现在飞书里跟我聊天。

---

## 一、飞书开放平台配置

### 1. 创建应用

1. 打开 [飞书开放平台](https://open.feishu.cn)
2. 点右上角 **"开发者后台"**
3. 点 **"创建应用"** → **"企业自建应用"**
4. 填写：
   - **应用名称**：`Hermes AI Agent`
   - **应用描述**：智能 AI 助手，支持天气查询、计算、对话
5. 点 **"确定创建"**

### 2. 获取凭证

1. 左侧菜单 → **"凭证与基础信息"**
2. 你会看到两个关键信息：
   - **App ID**：`cli_a978bd548cb89cd5`
   - **App Secret**：`cPOQNF5hA7NMurhMnbta1gbRRrEKqW5t`
3. 这两个值已经配置在 `feishu_config.sh` 中了

### 3. 配置事件回调

1. 左侧菜单 → **"事件与回调"**
2. 在 **"回调配置"** 区域：

   | 配置项 | 值 |
   |--------|-----|
   | 回调地址 | `https://machinery-cove-skill-nashville.trycloudflare.com/feishu/callback` |
   | 消息卡片签名 | 留空 |

3. 点 **"保存"**

### 4. 添加消息接收权限

1. 左侧菜单 → **"权限管理"**
2. 点 **"添加权限"**，搜索并勾选以下权限：
   - `im:message`（消息读写权限）
   - `im:message:send_as_bot`（以机器人身份发送消息）
   - `im:resource`（资源读写权限）
3. 点 **"批量申请"**

### 5. 订阅事件

1. 左侧菜单 → **"事件与回调"** → **"订阅事件"**
2. 点 **"添加事件"**
3. 搜索并勾选：
   - `im.message.receive_v1`（接收消息事件）
4. 点 **"确认添加"**

### 6. 发布应用

1. 左侧菜单 → **"版本管理与发布"**
2. 点 **"创建版本"**
3. 填写版本信息：
   - **版本号**：`1.0.0`
   - **更新说明**：首次发布，支持智能对话
4. 点 **"保存"**
5. 点 **"申请发布"**
6. 在审核页面点 **"前往企业自建应用审核"**
7. 搜索你的应用 → 点 **"审核"** → **"通过"**

### 7. 在飞书中使用

1. 打开飞书客户端
2. 搜索 **"Hermes AI Agent"**
3. 打开对话窗口，开始聊天！

---

## 二、本地服务说明

### 服务架构

```
你（飞书） → 飞书开放平台 → Cloudflare Tunnel → 本地 feishu_bot.py → DeepSeek API → 回复你
```

### 启动服务

```bash
cd ~/my-first-agent
bash run_feishu.sh
```

### 查看服务状态

```bash
# 飞书机器人服务
curl http://localhost:8655/health

# Cloudflare 隧道状态
curl -s https://machinery-cove-skill-nashville.trycloudflare.com/health
```

### 停止服务

```bash
# 停止飞书机器人
pkill -f feishu_bot.py

# 停止 Cloudflare 隧道
pkill -f cloudflared
```

### 一键启动所有服务

```bash
cd ~/my-first-agent
bash start.sh          # 启动网页版 + 自动同步
bash run_feishu.sh     # 启动飞书机器人
```

---

## 三、文件说明

| 文件 | 作用 |
|------|------|
| `feishu_bot.py` | 飞书机器人服务端代码 |
| `feishu_config.sh` | 飞书 App ID / Secret 配置 |
| `run_feishu.sh` | 启动脚本 |
| `feishu_setup_guide.md` | 本配置文档 |

---

## 四、故障排查

### 飞书机器人无回复

1. 检查本地服务是否运行：
   ```bash
   curl http://localhost:8655/health
   ```
2. 检查 Cloudflare 隧道是否正常：
   ```bash
   curl https://finding-thanks-raise-favor.trycloudflare.com/health
   ```
3. 检查飞书回调配置中的地址是否匹配当前隧道的地址
4. 检查飞书应用是否已发布并启用

### 隧道地址变了

每次重启 `cloudflared` 地址都会变。更新后需要：

1. 获取新地址：
   ```bash
   # 从 cloudflared 日志中找
   ```
2. 在飞书开放平台 → 事件与回调 → 更新回调地址
