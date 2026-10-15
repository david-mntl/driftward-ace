#!/usr/bin/env bash
# Contracts overview and checks.
# Usage: scripts/contracts.sh            what's in progress and ready to close out
#        scripts/contracts.sh verify     check headers, task pointers and INDEX.md
#        scripts/contracts.sh index      rebuild docs/contracts/INDEX.md
set -euo pipefail
exec python3 "$(dirname "$0")/python/contracts.py" "$@"
