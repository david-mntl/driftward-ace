# game: context for agents

Read this before you touch anything under `game/`.

## Good practice
- Follow the existing style of the file you edit. Run `game/tests/check.sh lint` before you hand off.
- Validate input at the edge, where data comes from a file, the browser or the player. Trust values inside `game/core/`.
- Keep functions short and names plain. No dead code, no commented-out code.
- Respect the tech rules in `docs/design/gdd/15-tech-constraints.md`: async main loop, no blocking calls, no threads, `.ogg` audio only.
- Shell scripts start with `set -euo pipefail`, quote every variable and clean up what they start. They log plain timestamped lines.

## Logging (rule)
Every agent that writes Python under `game/` follows this.
- Every module with code starts with `log = logging.getLogger(__name__)`. Use that logger, nothing else. A constants-only module (such as `app/settings.py`) has no logger.
- Only `game/app/log.py` configures logging: handlers, levels, format. No other code calls `logging.basicConfig`, adds a handler or sets a level.
- Levels and format are in `docs/design/gdd/15-tech-constraints.md`, section Values. Don't hard-code them anywhere else.
- **Log by event, never by tick.** Code that runs every tick logs only when something happens: a key pressed or released, a wall hit, a top-line stop, a respawn. Never a line every tick. Python in WebAssembly is slow and the console floods.
- Pick the level by what happened:
  - `DEBUG`: game events and state changes, useful only while debugging.
  - `INFO`: startup, run mode, screen changes.
  - `WARNING`: a problem the game recovered from, such as bad input that fell back to a default.
  - `ERROR`: a failure. Inside an `except`, use `log.exception(...)` so the traceback is kept.
- Lazy formatting: `log.debug("wall hit x=%s", x)`, never an f-string.
- No `print` in game code.

## Error handling (rule)
Every agent that writes Python under `game/` follows this.
- Catch the specific exception you expect. Never a bare `except`. `except Exception` is allowed in one place only: the top-level guard in `game/app/guard.py`.
- Never swallow an error. Log it and handle it, or let it rise.
- Validate at the edge (files, browser, player input). On bad data, raise with a message that says what was wrong and where. Trust values inside `game/core/`.
- `game/core/` and `game/ui/` raise. They never show an error on screen and never decide to keep running.
- The top-level guard logs the traceback at ERROR and switches to the error screen. The page never freezes silently.

## Run modes (rule)
- Two modes: normal (the default) and debug. The switches are in `docs/design/gdd/15-tech-constraints.md`.
- The mode is read once, at startup, in `game/app/`. Only `game/app/` and the debug overlay in `game/ui/` read it.
- `game/core/` behaves the same in both modes. Debug mode never changes a game rule.

## Layout
`main.py` opens with a PEP 723 inline-metadata block (`# /// script` … `# ///`) that lists `pygame-ce` under `dependencies`. This is pygbag's documented way to declare packages: pygbag installs only what `main.py` imports or declares. Without it the browser build has no pygame and crashes on import. Keep the block when you edit `main.py`, and add any new third-party package to it.

**Import boundary.** `main.py` and the startup modules in `app/` (`loop`, `mode`, `log`, `guard`, `settings`) import only the standard library at module level. Anything that imports pygame, `core` or `ui` is imported inside the guard, after logging is set up, so an import error is logged and shows the error screen instead of a blank page.

| Path | What it holds |
|---|---|
| `main.py` | entry point only: a PEP 723 header, then starts `app`. Nothing else |
| `app/` | startup: log setup, run mode, async loop, input reading, error guard |
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

The release package holds runtime files only. `pygbag.ini` at the repo root lists what pygbag leaves out (`[DEPENDENCIES] ignoreDirs`, `ignoreFiles`): `tests/`, `scripts/`, `CONTEXT.md` files, `requirements.txt`, `ruff.toml`. pygbag reads it from the folder it runs in, so run every build from the repo root. After a build, list the archive and confirm none of those files is in it.

### Browser
- A desktop run does not count. Every build is tested in a browser (`CLAUDE.md`).
- The console must have no errors. These pygbag lines are known and normal, and don't count:
  - "MEDIA USER ACTION REQUIRED" before the click.
  - A 404 for `browserfs.min.js` and "BrowserFS not found", on every page load. The file is missing from pygbag 0.9.3's own CDN.
  Any other error fails the check.
- In the browser, game logs reach the devtools console (`game/app/log.py` routes them there). Desktop runs log to stdout.
- Save screenshots outside the repo.
