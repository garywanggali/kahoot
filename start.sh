#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-5002}"
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
  echo "PORT must be a number" >&2
  exit 1
fi

# 服务器本地配置（不提交 git）：STEPFUN_API_KEY 等
if [ -f "local.env" ]; then
  # shellcheck disable=SC1091
  source local.env
fi

export DJANGO_DEBUG=False
export ALLOWED_HOSTS="110.40.153.38,localhost,127.0.0.1"
export CSRF_TRUSTED_ORIGINS="http://110.40.153.38:${PORT},http://localhost:${PORT}"
export TEACHER_PASSWORD="${TEACHER_PASSWORD:-teacher123}"

mkdir -p logs

if [ -f "logs/server.pid" ]; then
  OLD_PID="$(cat logs/server.pid || true)"
  if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
    echo "服务已在运行 (pid=${OLD_PID})，请先 ./stop.sh" >&2
    exit 1
  fi
fi

echo "[$(date '+%H:%M:%S')] 启动 0.0.0.0:${PORT} ..."
nohup venv/bin/daphne -b 0.0.0.0 -p "${PORT}" shoot_project.asgi:application \
  > logs/server.log 2>&1 &

echo $! > logs/server.pid
sleep 1

if kill -0 "$(cat logs/server.pid)" 2>/dev/null; then
  echo "[$(date '+%H:%M:%S')] OK pid=$(cat logs/server.pid)"
  echo "http://110.40.153.38:${PORT}/"
else
  tail -30 logs/server.log >&2 || true
  exit 1
fi
