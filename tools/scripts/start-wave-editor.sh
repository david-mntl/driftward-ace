#!/usr/bin/env bash
# Start the wave editor bench.
#
#   start-wave-editor.sh                  play the debug spawn list
#   start-wave-editor.sh game/waves/l1_a.json   play one wave, looped
#
# Paths are read from where you run the script. Needs python3 and pygame-ce.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"  # repo root
PY="${PYTHON:-python3}"

if ! "$PY" -c "import pygame" 2>/dev/null; then
    echo "pygame-ce is missing. Install it with: $PY -m pip install pygame-ce" >&2
    exit 2
fi

args=()
for arg in "$@"; do
    if [[ -e "$arg" ]]; then args+=("$(realpath "$arg")"); else args+=("$arg"); fi
done

export PYGAME_HIDE_SUPPORT_PROMPT=1
# The tool has no sound, and the dev container has no sound card or GPU. These stop the
# ALSA and MESA warnings. The window still opens, drawn in software.
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
# Run the editor as a child in its own process group, so cancelling the script (Ctrl+C, kill,
# closing the terminal) ends the editor and anything it started. Nothing is left behind.
set -m
"$PY" "$ROOT/tools/wave_editor/main.py" "${args[@]}" &
child=$!

cleanup() {
    trap - INT TERM HUP EXIT
    if kill -0 "$child" 2>/dev/null; then
        kill -TERM -- "-$child" 2>/dev/null
        for _ in {1..20}; do
            kill -0 "$child" 2>/dev/null || return 0
            sleep 0.1
        done
        kill -KILL -- "-$child" 2>/dev/null  # did not stop in 2 s
    fi
}
trap 'cleanup; exit 130' INT TERM HUP
trap cleanup EXIT

wait "$child"
exit $?
