#!/usr/bin/env bash
# Token use and cost per ticket and agent, from the Claude Code transcripts. Read-only.
# Usage: scripts/tokens.sh [--ticket DRA-29] [--by run] [--since YYYY-MM-DD] [--json]
set -euo pipefail
exec python3 "$(dirname "$0")/python/token_report.py" "$@"
