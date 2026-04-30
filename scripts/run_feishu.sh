#!/bin/bash
# 飞书机器人服务 - 启动脚本
# 接收飞书消息，转发给 Hermes Agent 处理，回复到飞书

cd "$(dirname "$0")/.."

# 检查配置
if [ ! -f "scripts/feishu_config.sh" ]; then
    echo "❌ 请先创建 scripts/feishu_config.sh，内容如下："
    echo ""
    echo 'export FEISHU_APP_ID="cli_xxxxxxxxxxxx"'
    echo 'export FEISHU_APP_SECRET="xxxxxx...xxxx"'
    echo ""
    echo "配置好后重新运行"
    exit 1
fi

source scripts/feishu_config.sh
source venv/bin/activate

echo "🚀 启动飞书机器人服务..."
echo "   端口: 8655"
echo "   接收地址: http://localhost:8655/feishu/callback"
echo ""
echo "   如需外网可访问，使用 cloudflared 或 ngrok:"
echo "   cloudflared tunnel --url http://localhost:8655"
echo ""

python src/feishu_bot.py
