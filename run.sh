#!/usr/bin/env bash
set -euo pipefail

# 日常启动：装依赖(仅必要时) + 迁移 + 静态文件 + 启动
#   ./run.sh 5002
# 强制重装依赖（很少需要）：
#   REBUILD_VENV=1 ./run.sh 5002

PORT="${1:-${PORT:-5002}}"
export PYTHONUNBUFFERED=1

log() {
  echo "[$(date '+%H:%M:%S')] $*"
}

chmod +x ensure_deps.sh start.sh 2>/dev/null || true
./ensure_deps.sh

# shellcheck disable=SC1091
source venv/bin/activate

log "数据库迁移..."
python manage.py migrate --noinput

log "公开题库样例..."
python manage.py seed_public_quizzes

log "收集静态文件..."
rm -rf staticfiles
python manage.py collectstatic --noinput

./start.sh "$PORT"
