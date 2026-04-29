#!/bin/bash
# 一键启动：网页服务 + 自动同步

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=============================="
echo "🚀 Hermes AI Agent - 启动"
echo "=============================="

# 1. 自动同步
echo ""
echo "📡 启动自动同步..."
cd "$PROJECT_DIR"
nohup bash auto-sync.sh > auto-sync.log 2>&1 &
echo "   PID: $!"

# 2. 网页服务器
echo "🌐 启动网页服务器..."
cd "$PROJECT_DIR"
source venv/bin/activate
nohup python web_chat.py > web_chat.log 2>&1 &
echo "   PID: $!"
echo "   http://localhost:8000"

# 局域网 IP
IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
if [ -n "$IP" ]; then
    echo "   手机: http://$IP:8000"
fi

echo ""
echo "✅ 启动完成"
echo "   停止同步: pkill -f auto-sync.sh"
echo "   停止网页: pkill -f web_chat.py"
echo "=============================="
