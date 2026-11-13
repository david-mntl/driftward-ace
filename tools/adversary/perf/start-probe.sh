#!/usr/bin/env bash
# Build a probed copy of the game in tools/adversary/out/perf/webbuild and serve it on port 6081.
# The repo's game/ is never changed. Stop with: kill "$(cat tools/adversary/perf/server.pid)"
set -euo pipefail
L=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$L/../../.." && pwd)
B=$L/../out/perf/webbuild
log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
if [[ -f "$L/server.pid" ]]; then kill "$(cat "$L/server.pid")" 2>/dev/null || true; sleep 2; fi
rm -rf "$B" && mkdir -p "$B"
B=$(cd "$B" && pwd)
cd "$REPO"
tar --exclude=game/build --exclude=__pycache__ --exclude=game/tests --exclude=game/x -cf - game web pygbag.ini | tar -xf - -C "$B"
cp "$L/probe.py" "$B/game/app/probe.py"
python - "$B/game/app/loop.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
hook = "    from app.frame import frame_loop\n"
if hook not in s:
    sys.exit("start-probe: the hook line in app/loop.py moved, so the probe would not load")
open(p, "w").write(s.replace(hook, "    import app.probe  # noqa: F401\n" + hook))
PY
cd "$B"
nohup python -m pygbag --port 6081 --template web/start.tmpl game > "$B/../server.log" 2>&1 &
echo $! > "$L/server.pid"
for _ in $(seq 1 60); do
  if curl -s -o /dev/null http://localhost:6081/; then log "probe served at http://localhost:6081"; exit 0; fi
  sleep 1
done
log "ERROR: server did not start, see out/perf/server.log"; exit 1
