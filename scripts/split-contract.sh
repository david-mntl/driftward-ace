#!/usr/bin/env bash
# One-time contract splitter. Dry-run unless --write is given. Run by the Director and the main session only.
# Usage: scripts/split-contract.sh split drifters [--detail] [--write]
#        scripts/split-contract.sh drop-impact run ship ... [--write]
set -euo pipefail
exec python3 "$(dirname "$0")/python/split_contract.py" "$@"
