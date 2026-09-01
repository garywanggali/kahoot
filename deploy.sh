#!/usr/bin/env bash
set -euo pipefail

SERVER="${1:-${DEPLOY_SERVER:-gary@110.40.153.38}}"
PORT="${2:-${DEPLOY_PORT:-5002}}"
REMOTE_DIR="${DEPLOY_DIR:-kahoot}"

echo "==> Upload to ${SERVER}:~/${REMOTE_DIR} port ${PORT}"
echo "==> Server venv and .requirements.hash will NOT be deleted"

rsync -avz --delete \
  --exclude venv \
  --exclude 'venv.*' \
  --exclude .requirements.hash \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  --exclude db.sqlite3 \
  --exclude .git \
  --exclude logs \
  --exclude staticfiles \
  --exclude media \
  ./ "${SERVER}:${REMOTE_DIR}/"

echo "==> Restart (skip pip if deps already installed)..."
ssh -t "${SERVER}" "cd ~/${REMOTE_DIR} && chmod +x run.sh stop.sh ensure_deps.sh start.sh check_python.sh && ./stop.sh || true && PYTHONUNBUFFERED=1 ./run.sh ${PORT}"

echo "==> Done: http://110.40.153.38:${PORT}/"
