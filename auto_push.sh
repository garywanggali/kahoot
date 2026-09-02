#!/usr/bin/env bash

# 自动同步脚本：实时检测本地文件变化并自动推送到 GitHub
# 仓库: https://github.com/garywanggali/kahoot.git

BRANCH="main"
REMOTE="origin"
INTERVAL=2  # 检查间隔（秒）

echo "=================================================="
echo " 🚀 Kahoot 实时自动同步已启动"
echo " 📁 监控目录: $(pwd)"
echo " 🔗 远程分支: ${REMOTE}/${BRANCH}"
echo " ⏱️  检测频率: 每 ${INTERVAL} 秒"
echo " (按 Ctrl+C 可停止实时同步)"
echo "=================================================="

while true; do
    # 检查是否有未暂存或已修改的文件
    if [ -n "$(git status --porcelain)" ]; then
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
        echo ""
        echo "[$TIMESTAMP] 🔍 检测到本地文件变更，正在同步到 GitHub..."
        
        git add -A
        git commit -m "auto-sync: $TIMESTAMP"
        
        if git push $REMOTE $BRANCH; then
            echo "[$TIMESTAMP] ✅ 成功推送到 GitHub!"
        else
            echo "[$TIMESTAMP] ❌ 推送失败，请检查网络或 GitHub 认证凭据。"
        fi
    fi
    sleep $INTERVAL
done
