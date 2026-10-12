Verdict: pass
Created by: integration-engineer

**Documentation differences come first (pending Director approval).** The DRA-5 contract can't be wired as written and still run in the browser. Two points need a contract change (D1, D2). Two need a Director call on the integration checks (D3, D4). Details are in item 5.

1. **Task:** integrate DRA-5 (game base: entry point, logging, run modes, loop, error guard). Requested in Integrate mode.
2. **Delivered:**
   - `game/main.py`: exactly the contract text.
   - `game/app/mode.py`, `game/app/log.py`, `game/app/guard.py`, `game/app/loop.py`.
   - `game/scripts/start-driftward-ace.sh`: added the `--debug` option and rejects unknown arguments.
   - `docs/reports/integration/DRA-5.md`: this report.
3. **Checks:**
   - Headless import of `app.loop`, `app.guard`, `app.log` and `app.mode` is clean (`SDL_VIDEODRIVER=dummy`).
   - `game/tests/check.sh` ends with `QA: pass` (lint, format and the ui tests pass).
   - `pygbag --archive game` built `game/build/web.zip` (exit 0, not committed). The zip holds `assets/main.py` and `assets/app/*.py`.
   - Browser run with `main.py` exactly as the contract gives it: the game crashed while importing, before the guard ran (bug D1). The canvas stayed 1x1 and the traceback went only to pygbag's hidden terminal.
   - Browser run with a temporary PEP 723 block in `main.py`: the game ran. I got `mode=debug`, `mode=normal`, and a WARNING then `mode=normal` for `?debug=yes`. The canvas was 640x480 and the center pixel black. Arrow keys logged their DEBUG lines.
   - All log lines appear only in pygbag's hidden xterm terminal, never in the devtools console (D2).
   - After that run I put `main.py` back to the contract text. See Browser run.
4. **Assumptions:**
   - `game/app/` has no `__init__.py`, the same as `game/ui/`. Namespace packages load in pygbag.
   - The browser switch is read with `platform.window.location.search` and `urllib.parse.parse_qs(..., keep_blank_values=True)`, so `?debug` and `?debug=` both return `""`.
   - `setup_logging` uses `logging.basicConfig(..., handlers=[one stdout handler], force=True)`, so exactly one handler stays, even if pygbag set up the root logger first.
   - `guard.py` has two `except Exception` blocks: one for the body, and one for the "error screen failed" step the contract asks for. Both are inside the guard module, the one place `game/CONTEXT.md` allows.
   - The start script exits with code 2 on a bad argument and prints the usage line to stderr.
5. **Documentation differences:** pending approval. All of them affect `docs/contracts/DRA-5/DRA-5-app.md` (Architect), and D2 also affects `docs/reports/scope/DRA-5.md`, Player sees.
   - **D1, Interface, `game/main.py`.** pygbag 0.9.3 decides which packages to install from `main.py` alone. It reads a PEP 723 block or scans that file's `import` lines (`pygbag/support/cpythonrc.py`, `preload_code`). The contract's `main.py` imports only `asyncio` and `app.loop`, so pygame-ce is never installed. `import pygame` then gives an empty namespace package, and `game/ui/error_screen.py:29` raises `AttributeError: module 'pygame' has no attribute 'Surface'` at import.
     - Proposed change: allow this comment block at the top of `main.py`, above the three lines. It adds no logic and no import:
       ```
       # /// script
       # dependencies = [
       #   "pygame-ce",
       # ]
       # ///
       ```
     - Proven in the browser: pygbag fetched `pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl` and the game started. The other option is `import pygame` in `main.py`, which the contract also forbids today.
   - **D2, Rules, Logging (`setup_logging`, "one handler: a StreamHandler on sys.stdout").** In pygbag 0.9.3, stdout and stderr both go only to its xterm terminal (`#pyconsole`, `display: none`). By default nothing reaches the devtools console (`pythons.js` stderr handler: `console.log` only when `vt.nodup` is off, and it is on). So the start line is visible nowhere. The scope report (Player sees: "the browser console shows a startup line") and the required check ("the start line is in the console") can't be met.
     - Proposed change: in the browser (`sys.platform == "emscripten"`), the one handler writes each formatted line to `platform.window.console.log`. On desktop it stays a `StreamHandler` on `sys.stdout`. Same format and same levels. Still one handler, in `app/log.py` only.
     - Proven reachable: a probe `platform.window.console.log('PROBE 14:30:00 INFO app.loop: start mode=debug')` showed up in the devtools console as `[LOG]`.
     - The Architect may want WARNING and ERROR lines to use `console.warn` and `console.error`. That is a contract choice, so I didn't make it.
   - **D3, required arrow-key check vs the contract.** The DRA-5 contract logs `key down key=up` and `key up key=up` without the ship x/y, and says DRA-6 adds them. DRA-5 has no ship. My required check needs the y in the key-down and key-up lines to change. Per my definition, that is a contract mismatch. It can't be run until DRA-6.
     - Proposed: the Director accepts, for DRA-5 only, "the key-down and key-up lines appear with the right key name" as the arrow-key check. The x/y check moves to DRA-6.
   - **D4, required check "no console errors" vs pinned pygbag.** Every page load logs two errors from pygbag's own loader, before any Python runs:
     - `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js`
     - `PyMain: BrowserFS not found`

     The file doesn't exist on the upstream CDN either: `https://pygame-web.github.io/cdn/0.9.3/browserfs.min.js` gives 404. The game runs fine after them. No game code can remove them while the pinned 0.9.3 default template is used.
     - Proposed: the Director adds these two lines to the known-normal pygbag lines in `game/CONTEXT.md`, INTEGRATION > Browser, the way "MEDIA USER ACTION REQUIRED" is listed. The other option is a custom pygbag template, but no lane owns a template file. That is an ownership gap for the roster.
6. **Next:**
   - Architect: amend the DRA-5 contract for D1 (allow the PEP 723 block in `main.py`) and D2 (browser log handler), after the Director approves.
   - Director: decide D3 (the DRA-5 arrow-key check without x/y) and D4 (accept the two pygbag loader errors, or a custom template and its owner).
   - Then re-run Integrate mode for DRA-5. The Architect was not started, because the verdict is blocked.
7. **Status:** blocked, waiting on the contract changes D1 and D2 and the Director's decisions on D3 and D4.

## Browser run
- **Build check:** `pygbag --archive game` built `game/build/web.zip` (exit 0). I rebuilt it at the end with the contract-exact `main.py`. It is not committed: `game/build/` is in `.gitignore`.
- **Served with** `game/scripts/start-driftward-ace.sh --debug`, in the background with its pid kept in the scratchpad. The log printed `Serving Driftward Ace at http://localhost:6060/?debug=1`. `curl` got 200.
- **Stopped** each time with `kill <script pid>`. The script's trap logged `Stopping server`, and port 6060 was free afterwards (checked twice).
- **Bad arguments:** `--bogus` gave `ERROR: Unknown argument: --bogus. Usage: start-driftward-ace.sh [--debug]` and exit 2. `--debug extra` also gave exit 2. Neither started anything.
- **pygbag and `?debug=1`:** pygbag printed `FLAGS : ... debug_user=false`, and `config.debug = false`. pygbag's own debug UI is turned on by the hash `#debug`, not by the query. `?debug=1` reached Python unchanged.

**Run 1: contract-exact `main.py` (`?debug=1`).**
- The build was served and the page loaded. After the click, the hidden pygbag terminal showed this traceback:
  `File "/data/data/game/assets/ui/error_screen.py", line 29 ... AttributeError: module 'pygame' has no attribute 'Surface'`
- In the browser, `pygame` was `_NamespacePath(['/data/data/org.python/assets/site-packages/pygame'])` with no attributes. pygame-ce was never installed (D1).
- Canvas 1x1, no start line. Required checks: **failed**.

**Run 2: temporary PEP 723 block in `main.py`, to test the D1 fix. Reverted afterwards.**
- Required, build served and loads: **passed**. Canvas 640x480, center pixel (0, 0, 0, 255).
- Required, start line: `14:28:53 INFO app.loop: start mode=debug`. It is in pygbag's hidden terminal, **not** in `browser_console_messages` (D2).
- Required, console errors: only the two pygbag loader errors (D4). There were no errors from game code, and no Python line reached the devtools console. The warnings are all pygbag and Chrome loader lines (iframe features, ScriptProcessorNode deprecation, VM prerun/postrun).
- Required, arrow keys (`?debug=1`):
  - ArrowUp pressed and released. Terminal: `14:29:19 DEBUG app.loop: key down key=up`, then `14:29:19 DEBUG app.loop: key up key=up`.
  - ArrowLeft: `key down key=left`, then `key up key=left`.
  - Key `a`: no line, as expected.
  - Ship x/y before and after: **not available**. DRA-5 has no ship and the contract logs no position (D3).
- Extra, normal mode (`/`): `14:29:50 INFO app.loop: start mode=normal`. ArrowUp logged nothing, which is right because DEBUG is filtered at INFO.
- Extra, rejected switch (`?debug=yes`): `14:30:16 WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `14:30:16 INFO app.loop: start mode=normal`.
- Extra, black 640x480 screen (scope, Player sees): canvas 640x480, pixel (320, 240) = (0, 0, 0, 255) in all three runs.

## Observations
- **Import errors are outside the guard.** In run 1 the error was raised while `main.py` imported `app.loop`, which imports `app.guard`, which imports `ui.error_screen` and `pygame`. That happens before `run()` and the guard exist. The page didn't show the error screen. It stayed on a 1x1 canvas, with the traceback only in the hidden terminal. The contract's Rationale accepts `read_switch` outside the guard, but not module imports. The Architect may want to cover this.
- The error screen path (guard, then `draw_error_screen`, then idle) was not shown in the browser. As the contract says, a browser run can't trigger it without a debug-only trigger. I checked it once headless: `guarded` with a body that raises `ValueError("boom\nsecond line")` logged `ERROR app.guard: unexpected error, showing the error screen` with the full traceback. `_detail` returns `ValueError: a b` in debug mode and `None` in normal mode.
- ArrowUp was pressed with Playwright `keyboard.press` (down then up). A longer hold was not needed, because DRA-5 has no state to change.
- A `beforeunload` dialog from pygbag blocked reloads in the same tab. I closed the tab and opened a new one for each run.
- Run 2 used a temporary `main.py`. The committed `main.py` is the contract-exact text and does **not** run in the browser until D1 is decided.

## Decisions
- **Loop.** Each frame: drain events, add the `time.perf_counter()` delta to the accumulator, take one step per whole 1/60 s (the DRA-5 tick does nothing), fill `ui.look.BACKGROUND`, `display.flip()`, `await asyncio.sleep(0)`. There is no catch-up cap; open question FL-04 is left for DRA-6. Source: contract Rules, Frame loop. 15-tech-constraints.md, rules 1 and 2.
- **Startup order:** `read_switch`, then `choose_mode`, then `setup_logging`, then the WARNING if a value was rejected, then INFO `start mode=%s`, then `guarded(_frame_loop, mode)`. `pygame.init()` and `set_mode` run inside the guard. Source: contract Rules, Startup.
- **Key logging.** One line per arrow `KEYDOWN`/`KEYUP` (`key down key=up` and so on). No other key is logged and nothing is logged per tick. Source: contract Rules, Frame loop. game/CONTEXT.md, Logging.
- **Idle after an error.** The guard's idle loop is written as `while True` with an early return on QUIT, instead of `while not ...: await sleep(0)`. That avoids ruff ASYNC110 and behaves the same. Source: contract Rules, Error guard, step 4.
- **Detail line.** The detail is built with `" ".join(text.splitlines())`, so every kind of newline becomes a space. Source: contract Rules, Error guard, step 2.
- **Start script.** It reads the argument before anything starts, and builds `URL` once for the `Serving` line. It keeps `set -euo pipefail`, the cleanup trap and no `--bind`. Source: contract Rules, Launch script. game/CONTEXT.md, INTEGRATION.
- **`main.py` put back to the contract text** after the D1 test, because I may not adapt the contract. Source: my definition, Failures.

## Round 1 2026-10-09

1. **Task:** re-run Integrate mode for DRA-5 after the Director decided D1 to D4. Requested by the Director.
2. **Delivered:**
   - `game/main.py`: the contract text, now with the PEP 723 block (D1).
   - `game/app/log.py`: one handler. In the browser it is `BrowserConsoleHandler`, which writes each formatted line with `platform.window.console.log`. On desktop it is still `StreamHandler(sys.stdout)` (D2).
   - `docs/reports/integration/DRA-5.md`: line 1 and this section.
   - Unchanged since round 0: `game/app/mode.py`, `game/app/guard.py`, `game/app/loop.py`, `game/scripts/start-driftward-ace.sh`.
3. **Checks:**
   - Headless import is clean. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy DRIFTWARD_DEBUG=1 timeout 3 python -c "import main"`, run from `game/`, logged `INFO app.loop: start mode=debug` to stdout, then `INFO app.loop: quit` when the timeout ended it.
   - `game/tests/check.sh` ends with `QA: pass`. env, lint, format and ui pass. core is skipped because it has no tests yet.
   - `pygbag --archive game` built `game/build/web.zip` (exit 0, 51279 bytes, git-ignored). Its `game.apk` holds `assets/main.py` with the PEP 723 block, plus `assets/app/*.py` and `assets/ui/*.py`.
   - All required browser checks passed. Details are in Browser run below.
4. **Assumptions:**
   - If `console.log` fails, `BrowserConsoleHandler.emit` catches only `AttributeError`, `TypeError` and `ValueError` and passes them to `logging.Handler.handleError`, as the standard handlers do. It doesn't use `except Exception`, because that is allowed only in the guard. The `handleError` output goes to pygbag's hidden terminal.
5. **Documentation differences:** None. D1 to D4 are now in the contract and `game/CONTEXT.md`, and this round follows them.
6. **Next:**
   - Architect started for close-out of DRA-5 (prompt: "Close-out run for DRA-5. Integration report: docs/reports/integration/DRA-5.md").
   - Director: run `game/scripts/start-driftward-ace.sh --debug` and open `http://localhost:6060/?debug=1`. Click the canvas, then open the devtools console. The build check is `pygbag --archive game`, which writes `game/build/web.zip`.
7. **Status:** done.

### Browser run
- **Build check:** `pygbag --archive game` built `game/build/web.zip` (exit 0). It is not committed.
- **Served with** `game/scripts/start-driftward-ace.sh --debug` in the background, pid in the scratchpad. The log printed `Serving Driftward Ace at http://localhost:6060/?debug=1`. `curl` got 200 after 2 s.
- **Stopped** with `kill <script pid>`. The trap logged `Stopping server (pid 196897)` and `Server stopped`. The script was gone about 1 s after the kill, no pygbag process was left, and port 6060 was free.
- The pygbag page was opened in a fresh tab for each URL (closed between runs).

**Required checks (`?debug=1`):**
- **Build is served and loads: passed.** The page title became `pygame window`. The `#canvas` was 640x480, pixel (320, 240) = (0, 0, 0, 255). pygbag fetched `pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl` (D1 works).
- **Start line in the console: passed.** `browser_console_messages` had `[LOG] 15:09:39 INFO app.loop: start mode=debug`.
- **No console errors: passed.** There were only two errors: `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`. Both are known-normal per `game/CONTEXT.md`, INTEGRATION > Browser (D4). No game code logged an error. The 16 warnings were all pygbag or Chrome loader lines: iframe features, FLAGS, vtx font, VM prerun and postrun, ScriptProcessorNode.
- **Arrow-key input: passed** on the key name, per the contract (D3). The canvas had focus.
  - ArrowUp pressed and released gave `15:09:55 DEBUG app.loop: key down key=up`, then `15:09:55 DEBUG app.loop: key up key=up`.
  - Ship x/y before and after: not applicable. DRA-5 has no ship, and the x/y comparison starts with DRA-6 (contract Rules, Frame loop; D3).

**Extra checks (from `docs/reports/scope/DRA-5.md` and the contract Rationale):**
- ArrowLeft logged `key down key=left`, then `key up key=left`. **Passed.**
- Key `a` logged no line. **Passed** (only arrow keys are logged).
- Normal mode (`/`) logged `[LOG] 15:10:08 INFO app.loop: start mode=normal`. ArrowUp then logged nothing, because DEBUG is filtered at INFO. Errors were the same two known pygbag lines. **Passed.**
- Rejected switch (`?debug=yes`) logged `[LOG] 15:10:27 WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `[LOG] 15:10:27 INFO app.loop: start mode=normal`. The canvas was 640x480 with pixel (320, 240) = (0, 0, 0, 255). **Passed.**
- Black 640x480 screen (scope, Player sees). **Passed** in the `?debug=1` and `?debug=yes` runs.

### Observations
- **Import errors are still outside the guard.** This is carried over from round 0. An error while `main.py` imports `app.loop` (and through it `app.guard`, `ui.error_screen`, `pygame`) happens before the guard exists. The page stays blank and the traceback goes only to pygbag's hidden terminal, because the console handler isn't set up yet either. D1 removes the cause seen in round 0. The gap in the contract remains, for the Architect to weigh.
- **The error screen path wasn't shown in the browser.** A browser run can't trigger it without a debug-only trigger, which the contract rules out. It is covered headless by task DRA-5-02. My round 0 headless check of the guard still applies, and `guard.py` hasn't changed since.
- **The game started before my click.** In the `?debug=1` run the start line is stamped 15:09:39, and my click came about 7 s later. No "MEDIA USER ACTION REQUIRED" line appeared. pygbag's own unlock flow seems to let this headless Chromium through. A real browser may still need the click. Nothing in DRA-5 depends on it.
- **The archive includes `game/tests/`.** pygbag packs the whole `game/` folder, so `assets/tests/conftest.py` and `assets/tests/ui/test_error_screen.py` ship in `game.apk`. They are never imported and are harmless, but they add weight to the release package. Excluding them is a build or packaging choice. No lane I know of owns it.
- **Arrow keys were sent as press-and-release.** Playwright `keyboard.press` sends down then up. A longer hold wasn't needed, because DRA-5 has no state to move.

### Decisions
- **The browser handler is a small `logging.Handler` subclass in `app/log.py`.** It is installed through the same `basicConfig(..., handlers=[handler], force=True)` call, so the root logger still has exactly one handler. Source: contract Rules, Logging. game/CONTEXT.md, Logging.
- **Every level uses `console.log`**, as the contract's Rationale records for D2.
- **`platform` is imported at module level in `app/log.py`,** the same as in `app/mode.py`. On desktop it is the stdlib module and is never touched. Only the browser branch uses `platform.window`. Source: contract Interface, `game/app/log.py`.
- **`main.py` is exactly the contract text.** Source: contract Interface, `game/main.py` (D1).

## Round 2 2026-10-09

1. **Task:** re-run Integrate mode for DRA-5 against the amended contract (import boundary, `pygbag.ini` release package, Integration checks). Requested by the Director.
2. **Delivered:**
   - `game/app/settings.py` (new): `TICK_RATE`, `SCREEN_SIZE`. Constants only, no imports.
   - `game/app/frame.py` (new): `ARROW_NAMES` and `frame_loop()`, moved from `loop.py`. Imports pygame, `ui.look` and `app.settings`.
   - `game/app/loop.py`: `run()` and `start()`. Module level is stdlib plus `app.guard`, `app.log` and `app.mode`. `start()` imports `app.frame` inside the guard.
   - `game/app/guard.py`: module level is stdlib plus `app.mode` and `app.settings`. The error step imports pygame and `ui.error_screen`, and opens the window if none exists. If that step fails, it logs `error screen failed` and returns without idling.
   - `pygbag.ini` (new, repo root): `[DEPENDENCIES]`, with `ignoreDirs` and `ignoreFiles`.
   - `docs/reports/integration/DRA-5.md`: this section.
   - No change since round 1: `game/main.py`, `game/app/mode.py`, `game/app/log.py` and `game/scripts/start-driftward-ace.sh`.
3. **Checks:**
   - **Import boundary:** importing `app.loop`, `app.guard`, `app.log`, `app.mode` and `app.settings` loads none of `pygame`, `ui`, `ui.look`, `ui.error_screen`, `app.frame` or `core` (checked in `sys.modules`).
   - **Headless import is clean.** From `game/`, with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy DRIFTWARD_DEBUG=1 timeout 3 python -c "import main"`, the log showed `INFO app.loop: start mode=debug`, then `INFO app.frame: quit` when the timeout stopped it.
   - **Import error, `app.frame` blocked** (`sys.modules['app.frame']=None; import main`, debug mode):
     - The log showed the start line, then `ERROR app.guard: unexpected error, showing the error screen` with the `ModuleNotFoundError: import of app.frame halted` traceback.
     - The process idled until `timeout` stopped it (exit 124).
     - A scratchpad probe ran the same blocked import, let `run()` go for 50 frames, then read the surface. The guard had opened a 640x480 window. The corner pixel was (0, 0, 0) and 1139 pixels were white (the text). The task was still idling.
   - **Import error, `pygame` blocked** (debug mode): the log showed the start line, then the first ERROR with its traceback, then `ERROR app.guard: error screen failed` with a second traceback (`guard.py` line 39, `import pygame`). The process ended by itself with exit 0, well inside the 10 s cap.
   - `game/tests/check.sh` ends with `QA: pass`: env, lint, format and ui pass. core is skipped because it has no tests yet.
   - **Build check:** `pygbag --archive game`, run from the repo root, built `game/build/web.zip` (exit 0, 37406 bytes, git-ignored). pygbag printed `Ignored dirs: ['/tests', '/scripts', '/.ruff_cache', '/.pytest_cache', '__pycache__']` and `Ignored files: ['CONTEXT.md', 'requirements.txt', 'ruff.toml']`.
   - **Package contents:** `game.apk` holds exactly these files: `assets/main.py`, `assets/app/{frame,guard,log,loop,mode,settings}.py` and `assets/ui/{error_screen,look}.py`. There are no tests, scripts, `CONTEXT.md`, `requirements.txt` or `ruff.toml`. The live build that the start script served (`game/build/web/game.apk`) holds the same 9 files.
   - All required browser checks passed. See Browser run.
4. **Assumptions:**
   - `ignoreDirs` entries start with `/`, for example `/tests`. pygbag 0.9.3 (`gathering.py`, `filtering.py`) matches folder paths relative to `game/` that start with `/`. A bare `__pycache__` matches that folder at any depth.
   - I added `/.ruff_cache`, `/.pytest_cache` and `__pycache__` beyond the contract's minimum list. They are tool caches, not runtime files. The contract says "any non-runtime file added to `game/` later is left out the same way". pygbag already skipped `.pyc` files, and `.ruff_cache` would otherwise ship its `CACHEDIR.TAG`.
5. **Documentation differences:** None. See Observations for one small mismatch between the contract and `game/CONTEXT.md` (`settings.py` and the logger line). I followed the contract.
6. **Next:**
   - Architect: I did not start it this round. It was already started for DRA-5 in round 1, and my rule allows that once per feature-id. If the close-out needs to run again on this round, the Director or `/implement` starts it with: "Close-out run for DRA-5. Integration report: docs/reports/integration/DRA-5.md".
   - Director: run `game/scripts/start-driftward-ace.sh --debug` and open `http://localhost:6060/?debug=1`, then open the devtools console. Build check: `pygbag --archive game` from the repo root writes `game/build/web.zip`.
7. **Status:** done.

### Browser run
- **Build check:** `pygbag --archive game` built `game/build/web.zip`. It is not committed.
- **Served with** `game/scripts/start-driftward-ace.sh --debug` in the background, with its pid in the scratchpad. The log printed `Serving Driftward Ace at http://localhost:6060/?debug=1`. `curl` got 200 after 2 s.
- **Stopped** with `kill <script pid>`. The trap logged `Stopping server (pid 200348)` and `Server stopped`. The script was gone, and port 6060 was free afterwards.
- Each URL ran in a fresh tab, closed between runs.

**Required checks (`?debug=1`):**
- **Build is served and loads: passed.** The title became `pygame window`. The canvas was 640x480, and pixel (320, 240) was (0, 0, 0, 255). pygbag fetched the `pygame_ce-2.5.7` wheel.
- **Start line in the console: passed.** `[LOG] 15:19:08 INFO app.loop: start mode=debug`.
- **No console errors: passed.** There were only the two known pygbag lines: the 404 for `browserfs.min.js` and `PyMain: BrowserFS not found`. The 16 warnings were all pygbag or Chrome loader lines.
- **Arrow keys: passed** on the key name (contract, Integration checks; D3). After clicking the canvas, ArrowUp, then ArrowLeft, then `a` were pressed:
  - `15:19:32 DEBUG app.frame: key down key=up`, then `key up key=up`
  - `key down key=left`, then `key up key=left`
  - nothing for `a`

  Ship x/y before and after: not applicable. DRA-5 has no ship, and the comparison starts with DRA-6. The logger name is now `app.frame`, because the loop moved there.

**Extra checks (contract Integration checks and scope report):**
- **Run modes: passed.**
  - `/` logged `[LOG] 15:19:54 INFO app.loop: start mode=normal`. ArrowUp then logged nothing, because DEBUG is filtered out.
  - `?debug=yes` logged `[LOG] 15:20:09 WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `[LOG] 15:20:09 INFO app.loop: start mode=normal`.
  - `?debug=1` reached Python unchanged. pygbag logged `orig_argv [debug=1]`, but `config.debug = false` and `debug_user=false`, so it did not switch into a mode of its own.
- **Black 640x480 screen: passed** in all three runs. Pixel (320, 240) was (0, 0, 0, 255).
- **Click to start: recorded** (see Observations). In all three runs the start line came before any click:
  - `?debug=1`: page opened at about 15:19:04, start line at 15:19:08, first click at about 15:19:25.
  - `/`: start line 15:19:54, click about 1 s later.
  - `?debug=yes`: never clicked, start line 15:20:09.

  No "MEDIA USER ACTION REQUIRED" line appeared in any run. No click prompt was visible. pygbag's `#infobox` held "Loading, please wait ..." but was hidden.
- **Package contents: passed.** See Checks.
- **Import errors: passed**, both cases. See Checks. These ran on desktop, headless, as the contract asks.

### Observations
- **The game starts before the click in this headless Chromium.** Before any click, `navigator.userActivation.hasBeenActive` was already `true` and pygbag's `MM.UME` was `true`, with `config.ume_block = 1`. So pygbag's media unlock passed on its own. No click screen showed and "MEDIA USER ACTION REQUIRED" never logged. The browser the Playwright tools drive seems to grant user activation up front. A normal desktop browser will likely show pygbag's click screen. I can't show that here. The contract says this doesn't fail DRA-5.
- **`settings.py` and the logger line.** The contract says `app/settings.py` is "Constants only. No imports." `game/CONTEXT.md`, Logging, says every module starts with `log = logging.getLogger(__name__)`. I followed the contract: the module has no import and no logger, and it never logs. The Architect may want to note this exception in `game/CONTEXT.md` or the contract.
- **The error screen was not shown in the browser.** As in rounds 0 and 1, a browser run can't trigger it without a debug-only trigger. The two import-error checks above cover it on desktop, headless.
- **Arrow keys were sent as press-and-release** with Playwright `keyboard.press`. DRA-5 has no state to hold a key against.

### Decisions
- **`start()` imports `app.frame` with a function-level import**, so the import runs inside `guarded`. Ruff, with the project rule set, accepts it. Source: contract Interface, `game/app/loop.py`. Rules, Import boundary.
- **The guard's error step is split in two.** `_show_error_screen()` is synchronous. It imports pygame and `ui.error_screen`, opens the window if `get_surface()` is `None`, draws and flips, and returns `False` after `log.exception("error screen failed")` if any of that raised. `_idle()` runs only when the step returned `True`. That keeps both `except Exception` blocks in `guard.py`, and a missing pygame can't reach the idle loop. Source: contract Rules, Error guard, steps 3 and 4.
- **`_idle()` imports pygame again inside the function.** It is the same module object the error step already loaded. This keeps pygame out of the module level. Source: contract Rules, Import boundary.
- **The window opened by the guard uses `SCREEN_SIZE` from `app.settings`**, the same value `frame_loop` uses. Source: contract Interface, `game/app/settings.py`.
- **`pygbag.ini` has a comment header** saying to build from the repo root. pygbag's parser (`configparser`, `;` comments) accepts it. Source: contract Interface, `pygbag.ini`. game/CONTEXT.md, INTEGRATION > Build check.
- **The frame loop code moved unchanged** from `loop.py` to `frame.py`. It is the same accumulator, fill, flip and `await asyncio.sleep(0)` as round 1. Source: contract Rules, Frame loop.
