#!/usr/bin/env bash
# Driftward Ace test harness. One entry point for lint, format and tests.
#
#   check.sh [all]              env, lint, format, core, ui
#   check.sh lint               ruff check + ruff format --check
#   check.sh core [pytest args] tests for game/core
#   check.sh ui [pytest args]   tests for game/ui
#   check.sh fix                ruff --fix + ruff format (implementers only)
#
# Last line is "QA: pass" or "QA: fail (<steps>)".
# Exit codes: 0 pass, 1 a check failed, 2 usage or env error.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 2  # game/

PY="${PYTHON:-python3}"
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy
export PYGAME_HIDE_SUPPORT_PROMPT=1

RESULTS=()
FAILED=()

record() {  # record <step> <PASS|FAIL|SKIP> [note]
    RESULTS+=("$(printf '%-5s %s' "$2" "$1")${3:+ $3}")
    if [[ "$2" == "FAIL" ]]; then FAILED+=("$1"); fi
}

header() {
    printf '\n== %s ==\n' "$1"
}

step_env() {
    header env
    "$PY" - <<'EOF'
import sys

assert sys.version_info[:2] == (3, 12), f"Python 3.12 required, got {sys.version.split()[0]}"
import pygame

assert pygame.IS_CE, "classic pygame installed, pygame-ce required"
import pytest
import ruff

print(f"python {sys.version.split()[0]}, pygame-ce {pygame.version.ver}, pytest {pytest.__version__}")
EOF
    if [[ $? -eq 0 ]]; then record env PASS; else record env FAIL; return 1; fi
}

step_lint() {
    header lint
    if "$PY" -m ruff check .; then record lint PASS; else record lint FAIL; fi
}

step_format() {
    header format
    if "$PY" -m ruff format --check .; then record format PASS; else record format FAIL; fi
}

step_pytest() {  # step_pytest <core|ui> [pytest args]
    local name="$1"
    shift
    header "$name"
    "$PY" -m pytest -c tests/pytest.ini "tests/$name" "$@"
    case $? in
        0) record "$name" PASS ;;
        5) record "$name" SKIP "(no tests yet)" ;;
        *) record "$name" FAIL ;;
    esac
}

summary() {  # summary [exit code on failure, default 1]
    header summary
    printf '%s\n' "${RESULTS[@]}"
    if [[ ${#FAILED[@]} -eq 0 ]]; then
        echo "QA: pass"
        exit 0
    fi
    echo "QA: fail (${FAILED[*]// /, })"
    exit "${1:-1}"
}

cmd="${1:-all}"
[[ $# -gt 0 ]] && shift

case "$cmd" in
    all)
        step_env || summary 2
        step_lint
        step_format
        step_pytest core
        step_pytest ui
        ;;
    lint)
        step_lint
        step_format
        ;;
    core | ui)
        step_pytest "$cmd" "$@"
        ;;
    fix)
        "$PY" -m ruff check --fix .
        "$PY" -m ruff format .
        exit $?
        ;;
    *)
        echo "usage: check.sh [all | lint | core [pytest args] | ui [pytest args] | fix]" >&2
        exit 2
        ;;
esac

summary
