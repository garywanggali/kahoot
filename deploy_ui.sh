#!/usr/bin/env bash
# 强制推送 UI 到服务器（不装依赖）
set -euo pipefail

SERVER="${1:-gary@110.40.153.38}"
PORT="${2:-5002}"
DIR="${3:-kahoot}"

echo "==> 1/3 上传 UI + 启动脚本 ..."
rsync -avz --progress \
  static/css/style.css \
  "${SERVER}:~/${DIR}/static/css/style.css"

rsync -avz --progress \
  templates/ \
  "${SERVER}:~/${DIR}/templates/"

rsync -avz \
  shoot_project/settings.py \
  start.sh stop.sh run.sh ensure_deps.sh \
  "${SERVER}:~/${DIR}/"

echo "==> 2/3 服务器重建 staticfiles 并重启 ..."
ssh -t "${SERVER}" bash -s <<REMOTE
set -euo pipefail
cd ~/${DIR}
chmod +x start.sh stop.sh run.sh ensure_deps.sh 2>/dev/null || true
source venv/bin/activate
export DJANGO_DEBUG=False
export ALLOWED_HOSTS='110.40.153.38,localhost,127.0.0.1'
export CSRF_TRUSTED_ORIGINS='http://110.40.153.38:${PORT},http://localhost:${PORT}'

echo "--- static/css/style.css ---"
head -3 static/css/style.css

rm -rf staticfiles
python manage.py collectstatic --noinput

echo "--- staticfiles/css/style.css ---"
head -3 staticfiles/css/style.css

./stop.sh || true
./start.sh ${PORT}
REMOTE

echo ""
echo "==> 3/3 验证 ..."
sleep 2
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://110.40.153.38:${PORT}/"
curl -s "http://110.40.153.38:${PORT}/static/css/style.css?v=3" | head -3
echo ""
echo "完成: http://110.40.153.38:${PORT}/ (Cmd+Shift+R 强刷)"
