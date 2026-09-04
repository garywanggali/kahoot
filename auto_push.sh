#!/usr/bin/env bash

# 实时双向自动同步脚本：实时拉取 (Pull) GitHub 最新内容 + 实时推送 (Push) 本地改动
# 仓库: https://github.com/garywanggali/kahoot.git

BRANCH="main"
REMOTE="origin"
INTERVAL=3  # 检查间隔（秒）

echo "=================================================="
echo " 🚀 Shoot 实时双向同步已启动"
echo " 📁 监控目录: $(pwd)"
echo " 🔗 远程分支: ${REMOTE}/${BRANCH}"
echo " ⏱️  检测频率: 每 ${INTERVAL} 秒 (实时 Pull + Push)"
echo " (按 Ctrl+C 可停止实时同步)"
echo "=================================================="

while true; do
    # 1. 检查是否有本地未提交的修改
    if [ -n "$(git status --porcelain)" ]; then
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
        echo ""
        echo "[$TIMESTAMP] 🔍 检测到本地修改，正在自动提交并推送..."
        git add -A
        git commit -m "auto-sync: $TIMESTAMP"
        
        # 先拉取最新避免冲突
        git pull --rebase $REMOTE $BRANCH >/dev/null 2>&1
        
        if git push $REMOTE $BRANCH; then
            echo "[$TIMESTAMP] ✅ 本地修改已成功推送到 GitHub!"
        else
            echo "[$TIMESTAMP] ❌ 推送失败，请检查网络连接或 GitHub 认证。"
        fi
    else
        # 2. 本地无修改时，静默拉取 GitHub 最新改动
        FETCH_OUT=$(git pull --rebase $REMOTE $BRANCH 2>&1)
        if echo "$FETCH_OUT" | grep -v -q "Already up to date."; then
            TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
            echo "[$TIMESTAMP] 📥 检测到 GitHub 远端有新更新，已自动实时 Pull 到本地！"
        fi
    fi
    
    sleep $INTERVAL
done
