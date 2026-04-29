#!/bin/bash
# 自动同步到 GitHub
# 用法: ./sync.sh "提交信息"

cd "$(dirname "$0")"

MSG="${1:-auto: update $(date '+%Y-%m-%d %H:%M')}"

git add -A
git diff --cached --quiet && echo "没有变化，跳过提交" && exit 0

git commit -m "$MSG"
git push
echo "✅ 已同步到 GitHub"
