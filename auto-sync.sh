#!/bin/bash
# 文件监听 + 自动提交 & 推送
# 后台运行：nohup bash ./auto-sync.sh &
# 停止：pkill -f auto-sync.sh

cd "$(dirname "$0")"
REPO_DIR="."

echo "📡 文件监听已启动，自动同步到 GitHub..."
echo "   停止: pkill -f auto-sync.sh"

while true; do
    # 检查是否有变化
    CHANGES=$(git -C "$REPO_DIR" status --porcelain 2>/dev/null | wc -l)
    
    if [ "$CHANGES" -gt 0 ]; then
        # 等待文件写完（防写了一半就提交）
        sleep 5
        
        # 再次检查
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
