#!/usr/bin/env bash
# 啟動 A股自選股智能分析系統（FastAPI 服務）
# 用法：./run.sh [額外參數，預設 --serve]
set -euo pipefail

# 切到腳本所在目錄，無論從哪裡呼叫
cd "$(dirname "${BASH_SOURCE[0]}")"

VENV=".venv"
PY="$VENV/bin/python"

# venv 不存在就建立並安裝依賴
if [[ ! -x "$PY" ]]; then
  echo "[run.sh] 找不到 $PY，建立 venv 並安裝依賴..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -r requirements.txt
fi

# 預設參數 --serve，可被命令列覆蓋
ARGS=("$@")
if [[ ${#ARGS[@]} -eq 0 ]]; then
  ARGS=(--serve)
fi

# 從參數解析 --port / --host（用於印出網址），預設 8000 / 0.0.0.0
PORT=8000
HOST="0.0.0.0"
for ((i=0; i<${#ARGS[@]}; i++)); do
  case "${ARGS[i]}" in
    --port)   PORT="${ARGS[i+1]:-$PORT}" ;;
    --port=*) PORT="${ARGS[i]#*=}" ;;
    --host)   HOST="${ARGS[i+1]:-$HOST}" ;;
    --host=*) HOST="${ARGS[i]#*=}" ;;
  esac
done
# 0.0.0.0 對使用者來說用 localhost 開比較直覺
DISPLAY_HOST="$HOST"
[[ "$HOST" == "0.0.0.0" ]] && DISPLAY_HOST="localhost"

echo ""
echo "  ➜  本機網站:  http://${DISPLAY_HOST}:${PORT}/"
echo "  ➜  API 文件:  http://${DISPLAY_HOST}:${PORT}/docs"
echo "     (Ctrl+C 停止)"
echo ""

exec "$PY" main.py "${ARGS[@]}"
