#!/usr/bin/env bash
# Contracts overview and checks.
# Usage: scripts/contracts.sh            what's in progress and ready to close out
#        scripts/contracts.sh verify     check headers, task pointers and INDEX.md
#        scripts/contracts.sh index      rebuild docs/contracts/INDEX.md and the hubs' part tables
#        scripts/contracts.sh interface game/core/drifters/satellite.py   sample of a generated Interface block, writes nothing
set -euo pipefail
exec python3 "$(dirname "$0")/python/contracts.py" "$@"
