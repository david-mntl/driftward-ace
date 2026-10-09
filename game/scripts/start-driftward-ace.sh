#!/usr/bin/env bash
# Build Driftward Ace with pygbag and serve it at http://localhost:6060
# Usage: game/scripts/start-driftward-ace.sh   (foreground, Ctrl+C stops it)
# Change the port with: PORT=7070 game/scripts/start-driftward-ace.sh
#
# The server stops when this script ends for any reason (Ctrl+C, kill, error,
# closed terminal). Stop it from another process with: kill <script pid>
#
# Do not add --bind. pygbag writes the bind address into the page's asset URLs,
# so a value other than localhost makes the browser block them and the page
# hangs on "Loading". VS Code forwards the port to the host.
set -euo pipefail

PORT="${PORT:-6060}"
STOP_TIMEOUT=5
SERVER_PID=""

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
err() { log "ERROR: $*" >&2; }

cleanup() {
  local status=$?
  trap - EXIT INT TERM HUP
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    log "Stopping server (pid ${SERVER_PID})"
    kill -TERM "${SERVER_PID}" 2>/dev/null || true
    for _ in $(seq 1 $((STOP_TIMEOUT * 10))); do
      kill -0 "${SERVER_PID}" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 "${SERVER_PID}" 2>/dev/null; then
      err "Server ignored SIGTERM after ${STOP_TIMEOUT}s, sending SIGKILL"
      kill -KILL "${SERVER_PID}" 2>/dev/null || true
    fi
    wait "${SERVER_PID}" 2>/dev/null || true
    log "Server stopped"
  fi
  exit "${status}"
}
# A signal turns into a normal exit, so the EXIT trap does the cleanup once.
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP

cd "$(dirname "$0")/../.."

if ! python -c "import pygbag" 2>/dev/null; then
  err "pygbag is not installed for $(command -v python || echo 'python'). Run: pip install -r game/requirements.txt"
  exit 1
fi

if (echo >"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then
  err "Port ${PORT} is already in use. Is the game already running? Try http://localhost:${PORT}"
  exit 1
fi

log "Serving Driftward Ace at http://localhost:${PORT}"
python -m pygbag --port "${PORT}" game &
SERVER_PID=$!
wait "${SERVER_PID}"
