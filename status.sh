#!/bin/bash
# Hermes 服务状态查看

echo "=============================="
echo " Hermes 服务状态"
echo "=============================="

echo ""
echo "📡 云隧道地址:"
curl -s --max-time 3 https://homework-elections-cellular-among.trycloudflare.com/health 2>/dev/null || echo "   ❌ 不可达"
echo ""

echo "🤖 飞书机器人 (8655):"
curl -s --max-time 3 http://localhost:8655/health 2>/dev/null || echo "   ❌ 未运行"
echo ""

echo "🌐 网页版 (8000):"
curl -s --max-time 3 http://localhost:8000/health 2>/dev/null || echo "   ❌ 未运行"
echo ""

echo "🔄 自动同步:"
ps aux | grep auto-sync | grep -v grep > /dev/null && echo "   ✅ 运行中" || echo "   ❌ 未运行"
echo ""
echo "=============================="
echo " 回调地址："
echo " https://homework-elections-cellular-among.trycloudflare.com/feishu/callback"
echo "=============================="
