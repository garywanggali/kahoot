#!/usr/bin/env bash
set -euo pipefail

if [ -f "logs/server.pid" ]; then
  PID="$(cat logs/server.pid)"
  if kill -0 "${PID}" 2>/dev/null; then
    echo "Stopping pid=${PID} ..."
    kill "${PID}"
    sleep 0.5
    if kill -0 "${PID}" 2>/dev/null; then
      kill -9 "${PID}" 2>/dev/null || true
    fi
  fi
  rm -f logs/server.pid
fi

pkill -f "daphne.*kahoot_project.asgi" 2>/dev/null || true
pkill -f "auto_push.sh" 2>/dev/null || true
echo "Stopped."
