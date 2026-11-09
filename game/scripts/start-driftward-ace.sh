#!/usr/bin/env bash
# Build Driftward Ace with pygbag and serve it at http://localhost:6060
# Usage: game/scripts/start-driftward-ace.sh               (foreground, Ctrl+C stops it)
#        game/scripts/start-driftward-ace.sh --debug       (same build, prints the debug URL)
#        game/scripts/start-driftward-ace.sh --wave w11    (debug mode, starts at a wave)
# --wave takes a wave id from game/waves, or its short start: w11 finds w11_lvl4_island.
# The run starts 3 s before the level-up into that wave's level, then plays the wave.
# With --wave the served page sends a plain http://localhost:6060 on to ?debug=1&wave=...,
# so any way you open the game starts at the wave while this script runs. The template is
# a temporary copy; web/start.tmpl is never changed.
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
READY_TIMEOUT=180
SERVER_PID=""
TEMPLATE="web/start.tmpl"
TEMP_DIR=""

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
  if [[ -n "${TEMP_DIR}" ]]; then
    rm -rf "${TEMP_DIR}"
  fi
  exit "${status}"
}
# A signal turns into a normal exit, so the EXIT trap does the cleanup once.
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP

USAGE="Usage: $(basename "$0") [--debug] [--wave <wave id>]"
DEBUG=0
WAVE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) DEBUG=1 ;;
    --wave)
      if [[ $# -lt 2 ]]; then
        err "--wave needs a wave id. ${USAGE}"
        exit 2
      fi
      WAVE="$2"
      DEBUG=1
      shift
      ;;
    *)
      err "Unknown argument: $1. ${USAGE}"
      exit 2
      ;;
  esac
  shift
done

cd "$(dirname "$0")/../.."

# Print the wave ids, one per line, for an error message.
list_waves() {
  local file
  for file in game/waves/*.json; do
    [[ "$(basename "${file}")" == "playlist.json" ]] && continue
    printf '  %s\n' "$(basename "${file}" .json)"
  done
}

# Find the wave file: the exact id first, then the one id that starts with "<id>_".
resolve_wave() {
  local id="${1%.json}"
  id="$(basename "${id}")"
  if [[ -f "game/waves/${id}.json" && "${id}" != "playlist" ]]; then
    printf '%s' "${id}"
    return 0
  fi
  local matches=()
  local file
  for file in game/waves/"${id}"_*.json; do
    [[ -f "${file}" ]] && matches+=("$(basename "${file}" .json)")
  done
  if [[ ${#matches[@]} -eq 1 ]]; then
    printf '%s' "${matches[0]}"
    return 0
  fi
  return 1
}

URL="http://localhost:${PORT}"
if [[ -n "${WAVE}" ]]; then
  if ! WAVE_ID="$(resolve_wave "${WAVE}")"; then
    err "No single wave matches '${WAVE}'. Waves:"
    list_waves >&2
    exit 2
  fi
  URL="${URL}/?debug=1&wave=${WAVE_ID}"
  log "Start wave: ${WAVE_ID}"
elif [[ "${DEBUG}" -eq 1 ]]; then
  URL="${URL}/?debug=1"
fi

if ! python -c "import pygbag" 2>/dev/null; then
  err "pygbag is not installed for $(command -v python || echo 'python'). Run: pip install -r game/requirements.txt"
  exit 1
fi

if (echo >"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then
  err "Port ${PORT} is already in use. Is the game already running? Try http://localhost:${PORT}"
  exit 1
fi

# Copy the template with a first line of script that sends a page opened with no query on to
# "?<query>". Sets TEMPLATE to the copy.
redirecting_template() {
  local query="$1"
  local line="if (!location.search) location.replace(location.pathname + \"?${query}\");"
  TEMP_DIR="$(mktemp -d)"
  TEMPLATE="${TEMP_DIR}/start.tmpl"
  awk -v add="${line}" '
    { print }
    !done && $0 == "--><script type=\"application/javascript\">" { print add; done = 1 }
  ' web/start.tmpl >"${TEMPLATE}"
  if ! grep -qF "${line}" "${TEMPLATE}"; then
    err "Could not add the wave redirect to web/start.tmpl: its first script block moved"
    exit 1
  fi
}

# Wait until the server answers, at most READY_TIMEOUT seconds. 1 if it stops or never answers.
wait_until_ready() {
  local i
  for ((i = 0; i < READY_TIMEOUT * 2; i++)); do
    kill -0 "${SERVER_PID}" 2>/dev/null || return 1
    (echo >"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null && return 0
    sleep 0.5
  done
  return 1
}

if [[ -n "${WAVE}" ]]; then
  redirecting_template "${URL#*\?}"
fi

log "Serving Driftward Ace at ${URL}"
python -m pygbag --template "${TEMPLATE}" --port "${PORT}" game &
SERVER_PID=$!
# pygbag prints hundreds of lines while it packs, so say the URL again once it serves.
if wait_until_ready; then
  log "Ready: ${URL}"
  if [[ -n "${WAVE}" ]]; then
    log "Plain http://localhost:${PORT} also starts at ${WAVE_ID} while this script runs."
  fi
fi
wait "${SERVER_PID}"
