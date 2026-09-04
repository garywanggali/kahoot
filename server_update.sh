#!/usr/bin/env bash
# 在服务器上日常更新：git pull + 迁移 + 静态文件 + 重启
set -euo pipefail

PORT="${1:-5002}"
DIR="${2:-$HOME/kahoot}"

cd "$DIR"

if [ ! -d .git ]; then
  echo "未检测到 .git，请先运行: ./server_init_git.sh" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1

echo "==> git pull"
git pull origin main

chmod +x ensure_deps.sh start.sh stop.sh run.sh server_init_git.sh server_update.sh 2>/dev/null || true
./ensure_deps.sh

source venv/bin/activate
export DJANGO_DEBUG=False
export ALLOWED_HOSTS='110.40.153.38,localhost,127.0.0.1'
export CSRF_TRUSTED_ORIGINS="http://110.40.153.38:${PORT},http://localhost:${PORT}"

python manage.py migrate --noinput
rm -rf staticfiles
python manage.py collectstatic --noinput

./stop.sh || true
./start.sh "$PORT"

echo "==> 已更新: http://110.40.153.38:${PORT}/"
