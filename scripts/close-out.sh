#!/usr/bin/env bash
# Close out a feature: show open findings and Observations, then freeze its contracts,
# set its tasks done and add the CHANGELOG entry. Writes only with --write.
# Usage: scripts/close-out.sh [FEATURE-ID] [--write --summary "One line." [--accept-open]] [--interfaces]
#        --interfaces (off by default) also regenerates the frozen contracts' Interface blocks from the code.
set -euo pipefail
exec python3 "$(dirname "$0")/python/contracts.py" close-out "$@"
