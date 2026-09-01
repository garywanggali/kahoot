#!/usr/bin/env bash
# 只负责虚拟环境和 pip，不启动服务
set -euo pipefail

export PYTHONUNBUFFERED=1
HASH_FILE=".requirements.hash"

log() {
  echo "[$(date '+%H:%M:%S')] $*"
}

find_python() {
  for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

deps_ready() {
  [ -x "venv/bin/daphne" ] && venv/bin/python -c 'import django, channels' 2>/dev/null
}

PYTHON="$(find_python || true)"
if [ -z "${PYTHON}" ]; then
  log "ERROR: 需要 Python 3.9+"
  exit 1
fi

if [ "${REBUILD_VENV:-0}" = "1" ] && [ -d "venv" ]; then
  log "REBUILD_VENV=1，删除旧 venv..."
  rm -rf venv
  rm -f "$HASH_FILE"
fi

if [ ! -d "venv" ]; then
  log "首次创建虚拟环境..."
  "${PYTHON}" -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

REQ_HASH="$(python -c "import hashlib; print(hashlib.md5(open('requirements.txt','rb').read()).hexdigest())")"
STORED_HASH=""
if [ -f "$HASH_FILE" ]; then
  STORED_HASH="$(cat "$HASH_FILE")"
fi

if deps_ready && [ "$REQ_HASH" = "$STORED_HASH" ]; then
  log "依赖已就绪，跳过 pip install"
  exit 0
fi

if deps_ready && [ "$REQ_HASH" != "$STORED_HASH" ]; then
  log "requirements.txt 变更，更新依赖..."
else
  log "首次安装依赖（约 2-5 分钟）..."
fi

python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements.txt
echo "$REQ_HASH" > "$HASH_FILE"
python -c "import django; print('Django', django.get_version())"
log "依赖安装完成"
