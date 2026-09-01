#!/usr/bin/env bash
# 在服务器上运行，检查 Python 环境
set -uo pipefail

echo "=== Python on this server ==="
for cmd in python3.12 python3.11 python3.10 python3.9 python3 python2; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo -n "$cmd: "
    "$cmd" --version 2>&1 || echo "failed"
  fi
done

echo ""
echo "=== pip (default python3) ==="
if command -v python3 >/dev/null 2>&1; then
  python3 -m pip --version 2>&1 || true
fi

echo ""
if [ -d venv ]; then
  echo "=== current venv ==="
  venv/bin/python --version 2>&1 || echo "venv broken"
else
  echo "No venv directory"
fi
