# game: context for agents

Read this before you touch anything under `game/`.

## Good practice
- Follow the existing style of the file you edit. Run `game/tests/check.sh lint` before you hand off.
- Handle errors on purpose. Catch the specific exception you expect, never a bare `except`. Don't swallow an error silently: log it, or let it fail loudly.
- Log when it helps someone find a problem later: startup, a failed load, an unexpected state. Use the `logging` module in game code and plain timestamped lines in shell scripts. No `print` in game code. No log inside the per-tick step.
- Validate input at the edge, where data comes from a file, the browser or the player. Trust values inside `game/core/`.
- Keep functions short and names plain. No dead code, no commented-out code.
- Respect the tech rules in `CLAUDE.md`: async main loop, no blocking calls, no threads, `.ogg` audio only.
- Shell scripts start with `set -euo pipefail`, quote every variable and clean up what they start.

## Layout
| Path | What it holds |
|---|---|
| `main.py` | entry point: async loop, input, calls into core and ui |
| `core/` | game rules, no pygame |
| `ui/` | drawing and screens |
| `scripts/` | helper scripts. `start-driftward-ace.sh` runs the game |
| `tests/` | the QA gate. See `tests/CONTEXT.md` |
| `build/` | pygbag output. Never commit it |

## INTEGRATION
Read this section first if you are the Integration Engineer.

### Run the game
The only way to run the game for a browser test is:

```
game/scripts/start-driftward-ace.sh
```

It builds with pygbag and serves at `http://localhost:6060`. Change the port with `PORT=<n>`. Never call `pygbag` with `--bind`: pygbag writes the bind address into the page's asset URLs, so any value but `localhost` makes the browser block them and the page hangs on "Loading".

The script stops the server when it ends, for any reason, so no server is left running. Start it, check the page, then stop it. Do not leave it for the Director to start.

1. Start it in the background and keep its pid:
   `game/scripts/start-driftward-ace.sh > "$LOG" 2>&1 & echo $! > "$PIDFILE"`
   Put `$LOG` and `$PIDFILE` in your scratchpad, not in the repo.
2. Wait until `http://localhost:6060` answers. Poll with `curl --max-time 2`, up to about 60 seconds. If it never answers, read the log and report `Verdict: blocked` with the last lines.
3. Open the page with the Playwright browser tools. pygbag shows "Loading, please wait" until the page is clicked. Click the canvas once, then run the checks.
4. When you finish, pass or fail, stop the server with `kill "$(cat "$PIDFILE")"`. The script's trap stops pygbag. Check the port is free. `pkill` is not installed here.

If the port is already in use, the script exits with a message. Another run may still be going. Don't kill a process you did not start. Report it.

### Build check
`pygbag --archive game` builds `game/build/web.zip`. That zip is the release package for static hosting (itch.io or GitHub Pages). It is a build check, not how you test. Run it to prove the package builds, and report the command and path. You never need to unzip it or serve it for the browser test: the script serves the live build.

### Browser
- A desktop run does not count. Every build is tested in a browser (`CLAUDE.md`).
- The console must have no errors. A pygbag line "MEDIA USER ACTION REQUIRED" before the click is normal.
- Save screenshots outside the repo.
