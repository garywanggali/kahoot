#!/usr/bin/env bash
# 在服务器上首次执行：把 rsync 目录转为 git 仓库（保留 venv、db.sqlite3）
set -euo pipefail

DIR="${1:-$HOME/kahoot}"
REPO="${2:-https://github.com/garywanggali/kahoot.git}"

cd "$DIR"

if [ -d .git ]; then
  echo "已是 git 仓库，跳过 init"
  git remote -v
  exit 0
fi

echo "==> 初始化 git 并关联 ${REPO}"
echo "    保留未纳入 git 的文件: venv/ db.sqlite3 logs/ staticfiles/"

git init -b main
git remote add origin "$REPO"
git fetch origin
git reset --hard origin/main

echo "==> 完成。之后更新用: ./server_update.sh"
echo "    当前版本:"
git log -1 --oneline
