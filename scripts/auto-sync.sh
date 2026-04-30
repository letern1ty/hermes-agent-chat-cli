#!/bin/bash
# 文件监听 + 自动提交 & 推送
# 使用：cd /path/to/project && bash scripts/auto-sync.sh
# 停止：pkill -f auto-sync.sh
#
# 用 git add -A 配合 .gitignore 自动忽略敏感文件
# .env、feishu_config.sh（含 App Secret）永远不会被提交

cd "$(dirname "$0")/.."
REPO_DIR="$(pwd)"

echo "📡 文件监听已启动，自动同步到 GitHub..."
echo "   🛡️   .env / feishu_config.sh 不会被提交（.gitignore 保护）"
echo "   停止: pkill -f auto-sync.sh"

while true; do
    CHANGES=$(git -C "$REPO_DIR" status --porcelain 2>/dev/null | wc -l)
    if [ "$CHANGES" -gt 0 ]; then
        sleep 5
        NEW_CHANGES=$(git -C "$REPO_DIR" status --porcelain 2>/dev/null | wc -l)
        if [ "$NEW_CHANGES" -gt 0 ]; then
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
            git -C "$REPO_DIR" add -A
            git -C "$REPO_DIR" commit -m "auto: sync $TIMESTAMP" 2>/dev/null
            if [ $? -eq 0 ]; then
                git -C "$REPO_DIR" push 2>/dev/null
                echo "✅ $TIMESTAMP - 已同步到 GitHub"
            fi
        fi
    fi
    sleep 30
done
