# App base: entry point, logging, run mode, loop, error guard, error screen
Version: 4
Status: frozen
Features: DRA-5, DRA-6, DRA-13, DRA-19
Created by: architect

## Purpose
Start the game, set up logging once, read the run mode once, run the async loop on the fixed 60 Hz tick, and catch any unexpected error so the page shows the error screen instead of freezing. That includes an error raised while importing pygame, core, the views or the frame loop. Build a release package that holds only runtime files.

From DRA-6, each tick steps the ship, each frame draws the ship and, in debug mode, the debug overlay. The arrow-key log lines carry the ship's x and y. F3 toggles the overlay in debug mode.

From DRA-13, play starts when the ship first appears: the app starts the world scroll right after it spawns the ship. Each tick also steps the scroll. Each frame draws the starfield behind the ship and the HUD on top of everything.

From DRA-19, the guard also removes null characters from the debug-mode detail line, so an error message holding one still shows the error screen.

Who builds what:
- `game/main.py`, `game/app/`, `game/scripts/`, `pygbag.ini` (repo root): the Integration Engineer, during integration, from this contract. No task file.
- `game/ui/look.py`, `game/ui/error_screen.py`: the UI Developer, task `DRA-5-01-ui-developer`.
- `game/tests/ui/test_error_screen.py`: the QA Engineer, task `DRA-5-02-qa-engineer`.
- `game/core/world.py`, `game/core/ship.py`: DRA-6, see `docs/contracts/DRA-6/DRA-6-world.md` and `docs/contracts/DRA-6/DRA-6-ship.md`. Core is the same in both modes.
- `game/ui/ship_view.py`, `game/ui/debug_overlay.py`: DRA-6, see `docs/contracts/DRA-6/DRA-6-ship.md` and `docs/contracts/DRA-6/DRA-6-debug-overlay.md`.
- `game/core/scroll.py`, `game/ui/starfield.py`: DRA-13, see `docs/contracts/DRA-13/DRA-13-scroll.md`.
- `game/ui/hud.py`: DRA-13, see `docs/contracts/DRA-13/DRA-13-hud.md`.

## Diagram
```mermaid
flowchart TD
  M["main.py<br/>asyncio.run(run())"] --> R["app.loop.run()"]
  R --> S["app.mode.read_switch()"]
  S --> C["app.mode.choose_mode(raw)"]
  C --> L["app.log.setup_logging(mode)"]
  L --> W{"rejected value?"}
  W -- yes --> WL["log WARNING once"]
  W -- no --> I
  WL --> I["log INFO start mode=..."]
  I --> G["app.guard.guarded(partial(start, mode), mode)"]
  G --> B["start(mode): import app.frame<br/>(pygame, core, ui), then frame_loop(mode):<br/>pygame init, window, frames"]
  B -- unexpected error,<br/>import errors included --> E["log.exception"]
  E --> X["import pygame, core.world and ui.error_screen,<br/>open the window if none,<br/>draw_error_screen, flip"]
  X -- ok --> ID["idle until the page closes"]
  X -- fails --> XF["log.exception('error screen failed')<br/>return"]
```

Import boundary. Everything above the guard imports only the standard library and other startup modules. pygame, `ui` and `core` are imported for the first time inside the guard.
```mermaid
flowchart LR
  subgraph startup["startup modules: stdlib only at module level"]
    MA["main.py"] --> LO["app.loop"]
    LO --> MO["app.mode"]
    LO --> LG["app.log"]
    LO --> GU["app.guard"]
    ST["app.settings"]
  end
  subgraph guarded["imported inside the guard"]
    FR["app.frame"] --> PG["pygame"]
    FR --> CW["core.world"]
    FR --> CS["core.ship"]
    FR --> CC["core.scroll"]
    FR --> UL["ui.look"]
    FR --> SF["ui.starfield"]
    FR --> SV["ui.ship_view"]
    FR --> DO["ui.debug_overlay"]
    FR --> HU["ui.hud"]
    ES["ui.error_screen"] --> PG
  end
  LO -. "start(mode), inside guarded" .-> FR
  GU -. "error step, inside the guard" .-> ES
  GU -. "error step, inside the guard" .-> CW
  FR --> ST
```

```mermaid
flowchart LR
  F["frame start"] --> EV["read events<br/>(quit, arrow keys with ship x/y,<br/>F3 in debug mode)"]
  EV --> HK["thrust = held arrow keys"]
  HK --> AC["add frame time<br/>to accumulator"]
  AC --> T{"acc >= 1/60 s<br/>and ticks < 5?"}
  T -- yes --> TK["one tick:<br/>ship = step(ship, thrust)<br/>scroll = step_scroll(scroll)"] --> T
  T -- no --> CAP{"acc still >= 1/60 s?"}
  CAP -- yes --> DROP["acc = 0<br/>(owed time dropped)"] --> D
  CAP -- no --> D["draw: fill ui.look.BACKGROUND,<br/>draw_starfield, draw_ship,<br/>draw_debug_overlay if overlay_visible,<br/>then draw_hud"]
  D --> FL["display.flip()"]
  FL --> Y["await asyncio.sleep(0)"]
  Y --> F
```

## Interface
Import root is `game/`, as in the tests: `from app.loop import run`, `from ui.error_screen import draw_error_screen`.

### game/main.py (Integration Engineer)
```python
# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///
import asyncio

from app.loop import run

asyncio.run(run())
```
Nothing else. No logic, no imports beyond these. The opening block is PEP 723 inline metadata. It is pygbag's documented way to declare packages: pygbag installs only what `main.py` imports or declares, so without it the browser build has no pygame-ce. Any new third-party package goes into this block. Source: Director decision D1 (DRA-5 integration). game/CONTEXT.md, Layout.

### game/app/mode.py (Integration Engineer)
```python
class RunMode(Enum):
    NORMAL = "normal"
    DEBUG = "debug"

@dataclass(frozen=True)
class ModeChoice:
    mode: RunMode
    rejected: str | None   # the switch value that was present but not "1"; None otherwise

def read_switch() -> str | None: ...
    # Browser (sys.platform == "emscripten"): the first value of URL query parameter `debug`.
    # Desktop: environment variable DRIFTWARD_DEBUG.
    # None when the switch is absent. Present with an empty value returns "".

def choose_mode(raw: str | None) -> ModeChoice: ...
    # Pure. No logging, no I/O.
```

### game/app/log.py (Integration Engineer)
```python
def setup_logging(mode: RunMode) -> None: ...
    # The only place that configures logging. Called once, at startup.
    # Installs exactly one handler on the root logger:
    #   browser (sys.platform == "emscripten"): writes each formatted line
    #     with platform.window.console.log
    #   desktop: logging.StreamHandler(sys.stdout)
```

### game/app/guard.py (Integration Engineer)
```python
async def guarded(body: Callable[[], Awaitable[None]], mode: RunMode) -> None: ...
    # Awaits body(). Holds the project's only `except Exception`.
    # Module level: stdlib and app.mode only. pygame, core.world and
    # ui.error_screen are imported inside the error step, never at the top.
```

### game/app/settings.py (Integration Engineer)
```python
TICK_RATE: int = 60                         # 15-tech-constraints.md, tick_rate
MAX_TICKS_PER_FRAME: int = 5                # 15-tech-constraints.md, max_ticks_per_frame (guess)
```
Constants only. No imports. From DRA-6 the screen size lives in `core/world.py` (`SCREEN_W`, `SCREEN_H`), and `SCREEN_SIZE` is removed from here. See Impact.

### game/app/loop.py (Integration Engineer)
```python
async def run() -> None: ...
    # Startup order, then guarded(functools.partial(start, choice.mode), choice.mode).

async def start(mode: RunMode) -> None: ...
    # The guarded body. Imports app.frame here, inside the guard, then awaits frame_loop(mode).
```
Module level: stdlib, `app.mode`, `app.log` and `app.guard` only. No pygame, no `core`, no `ui`, no `app.frame`.

### game/app/frame.py (Integration Engineer)
```python
ARROW_NAMES: dict[int, str]   # pygame.K_UP -> "up", K_DOWN -> "down", K_LEFT -> "left", K_RIGHT -> "right"

async def frame_loop(mode: RunMode) -> None: ...
    # pygame init, window, frames until pygame.QUIT.
    # Owns: ship (core.ship.Ship), scroll (core.scroll.Scroll), thrust (core.ship.Thrust),
    #       overlay_visible (bool).
```
Imports pygame, `app.settings`, `app.mode`, `core.world`, `core.ship`, `core.scroll`, `ui.look`, `ui.starfield`, `ui.ship_view`, `ui.debug_overlay` and `ui.hud`. Only `start()` imports this module, inside the guard.

App-owned state in `frame_loop`:
```python
ship: Ship              # core.ship.spawn() before the first frame; replaced by step() every tick
scroll: Scroll          # core.scroll.start_scroll() right after spawn(); replaced by step_scroll() every tick
thrust: Thrust          # rebuilt once per frame from the held arrow keys
overlay_visible: bool   # True from the first frame in debug mode, always False in normal mode.
                        # F3 flips it, debug mode only.
```

### pygbag.ini (repo root, Integration Engineer)
```ini
[DEPENDENCIES]
ignoreDirs = [...]    # folders under game/ left out of the package
ignoreFiles = [...]   # files under game/ left out of the package
```
pygbag 0.9.3 reads it from its working directory. The start script and the build check both run pygbag from the repo root. Source: Director decision (DRA-5 close-out, round 1 observations). docs/crew/roster.md, row 12.

DRA-6 calls, all made by `frame_loop`. Their signatures are set in the DRA-6 contracts:
```python
# before the first frame:
ship = spawn()                                  # DRA-6-ship.md
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
ship = step(ship, thrust)                       # DRA-6-ship.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_ship(surface, ship)                        # DRA-6-ship.md
if overlay_visible:
    draw_debug_overlay(surface, ship)           # DRA-6-debug-overlay.md
```

DRA-13 calls, all made by `frame_loop`. Their signatures are set in the DRA-13 contracts. The full order, with the DRA-6 calls in place:
```python
# before the first frame:
ship = spawn()
scroll = start_scroll()                         # DRA-13-scroll.md, right after spawn(): play starts
# per tick, inside the accumulator loop:
ship = step(ship, thrust)
scroll = step_scroll(scroll)                    # DRA-13-scroll.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, scroll)                 # DRA-13-scroll.md, behind everything
draw_ship(surface, ship)
if overlay_visible:
    draw_debug_overlay(surface, ship)
draw_hud(surface, scroll, below_overlay=debug)  # DRA-13-hud.md, last; debug = mode is RunMode.DEBUG
```

### game/ui/look.py (UI Developer)
```python
BACKGROUND: tuple[int, int, int]   # 12-art-and-audio.md, placeholder_bg
```
The one home of the background color in code. `app/frame.py` and later views import it.

### game/ui/error_screen.py (UI Developer)
```python
def draw_error_screen(surface: pygame.Surface, detail: str | None) -> None: ...
```
`detail` is `None` in normal mode, and the one-line `<ErrorType>: <message>` text in debug mode. The app decides which. The view never reads the run mode.

### game/scripts/start-driftward-ace.sh (Integration Engineer)
```
start-driftward-ace.sh            # serves the build, prints http://localhost:<PORT>
start-driftward-ace.sh --debug    # same build, prints http://localhost:<PORT>/?debug=1
```

## Presentation
The app draws nothing itself beyond the background fill. The ship view and the debug overlay have their own Presentation sections in `docs/contracts/DRA-6/DRA-6-ship.md` and `docs/contracts/DRA-6/DRA-6-debug-overlay.md`. The starfield and the HUD have theirs in `docs/contracts/DRA-13/DRA-13-scroll.md` and `docs/contracts/DRA-13/DRA-13-hud.md`. The error screen reads no core state, only what the guard passes it.

| Input | Shown as |
|---|---|
| (always) | the whole surface filled with `BACKGROUND`, (0, 0, 0). Source: 12-art-and-audio.md, placeholder_bg (guess) |
| (always) | `Something broke. Reload the page.` in the default font (`pygame.font.Font(None, 24)`), color (255, 255, 255), centered horizontally and vertically on the surface. Source: 10-ui.md, error_screen, error_text_font, error_layout, error_text_color (guess) |
| `detail` is a string | `detail` in the default font at 16 px (`pygame.font.Font(None, 16)`), color (255, 255, 255), centered horizontally. Its top edge sits one line-height below the main line's top (the main font's `get_linesize()`), so it reads as the next line. Source: 10-ui.md, error_layout, debug_text_font, error_text_color (guess) |
| `detail` wider than the surface | cut from the end, one character at a time, until its rendered width fits the surface width. No ellipsis. Source: 10-ui.md, error_debug_line (guess) |
| `detail` is `None` | nothing below the main line |

- Centering uses `surface.get_size()`, never a hard-coded screen size.
- Text is rendered antialiased.
- The view only draws. It never flips the display, never logs per frame, never catches an error. If it fails, it raises.
- Logging: the module has `log = logging.getLogger(__name__)`. It may log one DEBUG line when the detail is cut, with the original and cut lengths. Nothing else.

## Rules
Startup (`app.loop.run`), in this order:
1. `raw = read_switch()`, then `choice = choose_mode(raw)`. Source: 15-tech-constraints.md, rule 7 (read once, at launch).
2. `setup_logging(choice.mode)`. Source: game/CONTEXT.md, Logging.
3. If `choice.rejected is not None`: one WARNING, `debug switch value %r is not 1, using normal mode`. Source: 15-tech-constraints.md, debug_switch_other_value.
4. One INFO line: `start mode=%s` with `choice.mode.value`. In the console this reads like `12:00:01 INFO app.loop: start mode=debug`. Source: DRA-5 scope report, Player sees.
5. `await guarded(functools.partial(start, choice.mode), choice.mode)`. Everything after logging setup runs inside the guard: importing `app.frame` (and through it pygame, `core` and `ui`), pygame init, the window and the loop. Source: 15-tech-constraints.md, rule 8. Director decision (DRA-5 close-out: import errors must be logged and show the error screen).

Import boundary:
- Startup modules are `main.py`, `app/loop.py`, `app/mode.py`, `app/log.py`, `app/guard.py` and `app/settings.py`. At module level they import only the standard library and each other. Never pygame, `ui`, `core` or `app.frame`. pygbag's built-in `platform` module counts as standard library here. Source: Director decision (DRA-5 close-out).
- pygame, `ui` and `core` are first imported inside the guard: by `start()` through `app.frame`, or by the guard's error step. So an import error in any of them is caught by the guard, after logging is set up.
- `main.py` keeps its exact text above: the PEP 723 block, `import asyncio`, `from app.loop import run`, `asyncio.run(run())`. Source: Director decisions D1 and DRA-5 close-out.
- What runs before the guard is limited to stdlib-only code: the startup module imports, `read_switch`, `choose_mode` and `setup_logging`. Errors there can't reach the guard. See Rationale.

Run mode (`choose_mode`):
- `None` (switch absent): normal, `rejected=None`, no log. Source: 15-tech-constraints.md, run_mode_default, debug_switch_other_value.
- `"1"`: debug. Source: 15-tech-constraints.md, debug_switch_browser, debug_switch_desktop.
- Any other string, including `"0"` and `""`: normal, `rejected=<that string>`. Source: 15-tech-constraints.md, debug_switch_other_value.
- The mode never changes after startup. Source: 15-tech-constraints.md, rule 7.
- In the browser only the URL is read. On desktop only the env var is read. They never conflict.

Logging (`setup_logging`):
- Root logger level: INFO in normal mode, DEBUG in debug mode. Source: 15-tech-constraints.md, log_level_normal, log_level_debug.
- Exactly one handler on the root logger. Any handler set up before it is replaced. Source: game/CONTEXT.md, Logging.
  - Browser (`sys.platform == "emscripten"`): each formatted line goes to the devtools console through `platform.window.console.log`, at every level. pygbag sends stdout and stderr only to its hidden terminal, so this is the only way the lines reach the console. Source: Director decision D2 (DRA-5 integration). game/CONTEXT.md, Browser.
  - Desktop: a `StreamHandler` on `sys.stdout`.
- Format `%(asctime)s %(levelname)s %(name)s: %(message)s`, date format `%H:%M:%S`. That gives `HH:MM:SS LEVEL logger: message`. Same format and levels on both targets. Source: 15-tech-constraints.md, log_format.
- No other code calls `basicConfig`, adds a handler or sets a level. Source: game/CONTEXT.md, Logging.
- Log by event, never by tick. Source: 15-tech-constraints.md, rule 9.

Frame loop (`app/frame.py`, `frame_loop(mode)`):
- Inside the guard: `pygame.init()`, then `pygame.display.set_mode((SCREEN_W, SCREEN_H))` from `core.world`. Source: 03-world-and-camera.md, screen_w, screen_h (guess). DRA-6-world.md.
- Before the first frame: `ship = spawn()`, then at once `scroll = start_scroll()`, and `overlay_visible = mode is RunMode.DEBUG`. Play starts here: the ship first appears at screen center on the first frame drawn after this. Source: 03-world-and-camera.md, ship_start; 10-ui.md, debug_overlay_toggle (shown from the first frame); scope report DRA-13, Values needed (play start); DRA-13-scroll.md.
- Nothing ever calls `start_scroll()` again in the run. A respawn is not a new play start. The scroll is never reset, paused or skipped. Source: 03-world-and-camera.md, rule 4; scope report DRA-13, Limits.
- Each frame, in order: read all events, build `thrust` from the held keys, add the frame time to the accumulator, run one tick per whole 1/60 s in the accumulator, draw, `pygame.display.flip()`, `await asyncio.sleep(0)`. Source: 15-tech-constraints.md, rules 1 and 2.
- Frame time comes from a monotonic clock (`time.perf_counter`). Ticks never use frame time. Source: 15-tech-constraints.md, rule 2.
- **Held keys.** After the events, read `pygame.key.get_pressed()` once and build `Thrust(up=pressed[K_UP], down=pressed[K_DOWN], left=pressed[K_LEFT], right=pressed[K_RIGHT])`. Every tick in that frame uses the same `thrust`. Only the four arrow keys move the ship. Source: 01-vision.md, locked decision 1; 04-ship.md, rule 2.1.
- **Tick.** `ship = step(ship, thrust)`, then `scroll = step_scroll(scroll)`. One call of each per tick, nothing else. The two never pass state to each other. Source: 04-ship.md, rules 1 and 3; 03-world-and-camera.md, rule 4; DRA-6-ship.md; DRA-13-scroll.md.
- **Draw.** In this order: fill with `ui.look.BACKGROUND`; `draw_starfield(surface, scroll)`; `draw_ship(surface, ship)`; `draw_debug_overlay(surface, ship)` only if `overlay_visible`; `draw_hud(surface, scroll, below_overlay=debug)` last, on top of everything. Source: DRA-6-ship.md, DRA-6-debug-overlay.md, DRA-13-scroll.md and DRA-13-hud.md, Presentation; 10-ui.md, rule 1 (the HUD on top); 12-art-and-audio.md, rule 2 (the background stays behind).
- **`below_overlay`** is `mode is RunMode.DEBUG`, fixed for the run. Never `overlay_visible`: in debug mode the HUD stays below the overlay's place while F3 hides it, so the readout never jumps. Source: scope report DRA-13, HUD layout.
- `pygame.QUIT`: log INFO `quit` and leave the loop. That only happens on desktop.
- **Arrow keys** (Up, Down, Left, Right): on `KEYDOWN` log DEBUG `key down key=%s x=%.2f y=%.2f`, on `KEYUP` log DEBUG `key up key=%s x=%.2f y=%.2f`, with names `up`, `down`, `left`, `right` and the ship's `x` and `y` at the moment the event is read (before this frame's ticks). Example: `key down key=up x=320.00 y=240.00`. No other arrow event is logged. Source: game/CONTEXT.md, Logging (a key pressed or released is an event). 01-vision.md, locked decision 1. Director decision (DRA-6: the integration check compares y between key-down and key-up).
- **F3.** In debug mode, on `KEYDOWN` of `pygame.K_F3`: flip `overlay_visible` and log DEBUG `overlay visible=%s`. `KEYUP` of F3 does nothing. In normal mode F3 does nothing and logs nothing. Source: 10-ui.md, debug_overlay_toggle (guess) and rule 7.
- **Log by event.** The frame loop logs only on the events in these rules: quit, arrow keys, F3 and the cap. Never a line per tick or per frame. Ship events (wall hit, top-line stop, respawn) are logged by `core.ship`, and the scroll start by `core.scroll`, not by the app. Source: 15-tech-constraints.md, rule 9; DRA-6-ship.md, Rules, Logging.
- **Catch-up cap.** One frame runs at most `MAX_TICKS_PER_FRAME` (5) ticks. If, after the 5th tick, the accumulator still holds one tick or more, set it to 0.0: the owed time is dropped, never run later. The game carries on from where it was. Source: 15-tech-constraints.md, max_ticks_per_frame (guess) and rule 2; 91-decision-log.md, row 21.
- **Cap log, by event.** Log DEBUG `tick cap hit, dropped %.3f s` (the seconds dropped) on a frame where the cap drops time and the frame before didn't. While frames keep hitting the cap, log nothing more. The next capped frame after an uncapped one logs again. Source: 15-tech-constraints.md, rule 9.
- No `time.sleep`, no thread, no blocking call. Source: 15-tech-constraints.md, rule 1.

Error guard (`app/guard.py`):
- The only `except Exception` in the game. Source: game/CONTEXT.md, Error handling.
- On an exception from `body`:
  1. `log.exception("unexpected error, showing the error screen")`. That is ERROR level with the full traceback. Source: 15-tech-constraints.md, rule 8.
  2. `detail = None` in normal mode. In debug mode, `detail = f"{type(exc).__name__}: {exc}"` with every newline replaced by a space, so it is one line, and every null character (`\x00`) removed, so the error screen can render it. Source: 10-ui.md, error_screen, error_debug_line. Null characters: scope report DRA-19, item 4; review DRA-5-01-ui-developer, finding 3; 15-tech-constraints.md, rule 8.
  3. Show the error screen, once. Source: 10-ui.md, rule 8. In this order:
     1. Import pygame, `core.world` and `ui.error_screen` here, inside the step. Source: Director decision (DRA-5 close-out).
     2. If `pygame.display.get_surface()` is `None` (the error came before the window existed, such as an import error in `app.frame`), call `pygame.init()` and `pygame.display.set_mode((SCREEN_W, SCREEN_H))` from `core.world`. If a window already exists, reuse it.
     3. `draw_error_screen(surface, detail)`, then `pygame.display.flip()`.
  4. Idle: each frame, drain the event queue and `await asyncio.sleep(0)`. No tick, no redraw. The game doesn't resume, and the player reloads the page. Source: 10-ui.md, rule 8. Leave the idle loop only on `pygame.QUIT` (desktop).
- If any part of step 3 raises, log it with `log.exception("error screen failed")` and return, without idling. That covers pygame missing or broken (an `ImportError`, or an `AttributeError` from an empty `pygame` namespace package as in round 0), `core.world` or `ui.error_screen` failing to import, the window failing to open, and the draw or flip failing. `run()` then returns, so nothing hangs. The page shows whatever was last drawn, and the console holds both tracebacks. Source: Director decision (DRA-5 close-out).
- Both tracebacks reach the console, because logging was set up before the guard started.
- `KeyboardInterrupt`, `SystemExit` and `asyncio.CancelledError` are not `Exception` and are not caught.
- Code outside `game/app/` never catches broadly, never shows an error on screen, and never decides to keep running. Source: game/CONTEXT.md, Error handling.

Launch script (`game/scripts/start-driftward-ace.sh`):
- `--debug`: same build and same server. The only difference is the printed URL, `http://localhost:${PORT}/?debug=1`. Source: 15-tech-constraints.md, debug_switch_launcher.
- No argument: unchanged behavior, prints `http://localhost:${PORT}`.
- Any other argument: print a usage line naming the bad argument to stderr and exit non-zero before starting anything.
- Keep the existing rules: `set -euo pipefail`, quoted variables, cleanup trap, never `--bind`. Source: game/CONTEXT.md, Good practice and INTEGRATION.
- Keep running pygbag from the repo root, so it reads `pygbag.ini`.

Release package (`pygbag.ini`):
- The package (`game.apk` inside `game/build/web.zip`, and the live build the start script serves) holds only runtime files: `main.py`, `app/`, `ui/`, `core/`, and later the asset and data files the game reads. From DRA-6, `core/*.py` must be in it. Source: Director decision (DRA-5 close-out, round 1 observations).
- Left out, at least: `tests/` (with its `CONTEXT.md` and `conftest.py`), `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`. Any non-runtime file added to `game/` later is left out the same way. Source: Director decision (DRA-5 close-out).
- Configured only in `pygbag.ini` at the repo root, `[DEPENDENCIES]` section, `ignoreDirs` and `ignoreFiles`. Built by the Integration Engineer. Source: Director decision (DRA-5 close-out). docs/crew/roster.md, row 12.
- No pygbag flag or template change. pygbag stays at 0.9.3. Source: 15-tech-constraints.md, web_build.

How the browser checks below are done. These methods are the checks as written, not stand-ins, so using them is never an observation on its own. Source: Director decision (DRA-19 close-out).
- **Screenshot** means reading the canvas pixels and comparing them with the expected color or text, for example text drawn in the same page with the game's own font. A pixel match counts as the screenshot.
- **Hide the tab** means freezing the page's main thread for the stated time, then letting it run again. For the game this is the same thing: one long gap between frames.
- **Real browser behavior** (pygbag's click screen, a truly hidden tab) can only be seen in a desktop browser. The Director checks it by hand when the frame loop or start-up changes, and before a release. The click-to-start checks below still record what they ask for, in Browser run. They go under Observations only when the result differs from the earlier runs (the game starting before any click, in the test browser, is the known result).

Integration checks for DRA-5, on top of the required browser checks in game/CONTEXT.md, INTEGRATION:
- **Arrow keys:** passes when the key-down and key-up lines appear with the right key name. DRA-5 has no ship, so there is no x/y to compare. That comparison starts with DRA-6. Source: Director decision D3 (DRA-5 integration).
- **Run modes:** no switch logs `start mode=normal`. `?debug=1` logs `start mode=debug`. `?debug=yes` logs one WARNING, then `start mode=normal`. `?debug=1` reaches Python unchanged and doesn't switch pygbag into a mode of its own.
- **Click to start:** record whether pygbag's click screen shows, whether "MEDIA USER ACTION REQUIRED" appears, and the time of the start line against the time of the click. Report what happened. A game that starts before the click doesn't fail DRA-5. It goes under Observations only as the "How the browser checks are done" rules above say. Source: Director decision (DRA-5 close-out, round 1 observations: follow up; DRA-19 close-out).
- **Package contents:** list the files in `game.apk` from `pygbag --archive game`. None of the left-out files may be there, and `main.py`, `app/*.py` and `ui/*.py` must be.
- **Import errors (desktop, headless, `SDL_VIDEODRIVER=dummy`):** no code change, only a blocked import from the command line.
  - Block `app.frame` (for example `sys.modules["app.frame"] = None` before `import main`): the log shows the start line, then ERROR `unexpected error, showing the error screen` with the `ImportError` traceback. The error screen is drawn and the process idles until it is stopped.
  - Block `pygame` the same way: the log shows the start line, the ERROR with the traceback, then ERROR `error screen failed` with its own traceback. The process ends by itself and doesn't hang.

Integration checks for DRA-6, on top of the required browser checks and every DRA-5 check above (all must still pass). Background: with no key held, the ship falls off the floor and respawns about once a second.
- **Arrow keys with x/y (`?debug=1`):** hold ArrowUp for about 2 s (`keyboard.down`, wait, `keyboard.up`). The key-down and key-up lines both carry `x=` and `y=`. The key-up `y` is smaller than the key-down `y`, and after a 2 s hold it is `184.00` (top edge on the top line). Source: Director decision (DRA-5 integration, D3; DRA-6 design input).
- **Log by event, not by tick (`?debug=1`):** hold ArrowUp and ArrowLeft together for about 3 s. Between that key-down and key-up there is exactly one `top line stop` line and exactly one `wall hit side=left` line. With no key held for 5 s, the only new lines are `respawn from ...`, about one a second, never one per tick. From DRA-13, the one `scroll start` line may also fall in that window if it covers the first 0.5 s of play. Source: 15-tech-constraints.md, rule 9; DRA-6-ship.md, Rules, Logging.
- **Respawn (`?debug=1`):** after the keys are released, a `respawn from x=... y=...` line appears within about 2 s, with `y` at least 496.00 (top edge at or past 480). Source: DRA-6 scope report, Limits.
- **Ship visible (`/`):** the canvas shows white (255, 255, 255) pixels (the ship) and no (0, 255, 0) pixels. F3 logs nothing and changes nothing. Source: DRA-6-ship.md, Presentation; 10-ui.md, rule 7.
- **Overlay and F3 (`?debug=1`):** from the first frame there are (0, 255, 0) pixels on row 168, away from the ship. F3 logs `overlay visible=False` and those pixels go to the background color. F3 again logs `overlay visible=True` and they come back. Source: 10-ui.md, debug_overlay, debug_overlay_toggle.
- **Click to start, follow-up:** the Director asked for this again, because in DRA-5 headless Chromium skipped the click. Record, in a fresh tab: whether pygbag's click screen shows, whether "MEDIA USER ACTION REQUIRED" appears, `navigator.userActivation.hasBeenActive` before any click, the time of the start line, and whether `respawn` lines appear before the click (the ship already moving). Report what happened in Browser run, and under Observations only as the "How the browser checks are done" rules above say. A game that starts before the click doesn't fail DRA-6. A game that doesn't start after a click fails it. Source: Director decision (DRA-5 close-out, follow up; DRA-6 design input; DRA-19 close-out).
- **Catch-up cap (`?debug=1`):** hide the tab for about 5 s (see "How the browser checks are done" above), then let it run. One `tick cap hit, dropped ... s` line appears, with about the hidden time. It is not repeated every frame. The game carries on: the ship doesn't jump ahead by the hidden time, and the respawn lines stay about one a second. Source: 15-tech-constraints.md, max_ticks_per_frame, rules 2 and 9; Director decision (DRA-19 close-out).
- **Package contents:** as for DRA-5, and `core/world.py`, `core/ship.py`, `ui/ship_view.py` and `ui/debug_overlay.py` must be in `game.apk`.

Integration checks for DRA-13, on top of the required browser checks and every DRA-5 and DRA-6 check above (all must still pass). Background: 1.1 px a tick at 60 ticks a second is 66 px, so 6.6 m, a second. The readout gains about 66 m in 10 s.
- **Scroll start, logged once (`?debug=1`):** exactly one `scroll start tick=31` line after the start line. In about 10 s of play no second one appears, including across several `respawn from` lines. Source: DRA-13-scroll.md, Rules, Logging; 03-world-and-camera.md, rule 4.
- **Readout counts up (`/`):** a screenshot right after play starts shows `0 m` at the top-left, with its text top near y 24. Screenshots about 5 s and 10 s later, with no key held (the ship falling and respawning), show larger whole numbers, the 10 s one about 66 m. Within a run the number never goes down. Source: scope report DRA-13, Player sees; DRA-13-hud.md, Layout.
- **Hovering still earns meters (`/`):** hold ArrowUp for about 5 s so the ship sits on the top line. The readout keeps counting at the same rate as with no key held. Source: 03-world-and-camera.md, Edge cases.
- **Starfield moves (`/`):** the canvas has (90, 100, 140) pixels. Two screenshots about 1 s apart, after the first 0.5 s, show the dots about 66 px lower, with dots that left the bottom back at the top. In the first 0.5 s after play starts they sit still. Source: DRA-13-scroll.md, Presentation.
- **No overlap in debug mode (`?debug=1`):** the four green overlay lines sit at the top-left, and the white readout sits below the last one, with a gap and no shared pixel row. Press F3: the overlay text goes away and the readout stays exactly where it was. F3 again brings the overlay back, still with no overlap. The overlay shows only x, y, vx and vy and its two lines, as in DRA-6. Source: DRA-13-hud.md, Rules; scope report DRA-13, Decision log.
- **Top line is still a ceiling (`?debug=1`):** the DRA-6 ArrowUp check still ends at `y=184.00`. Source: DRA-6-ship.md, step 7.
- **Package contents:** as for DRA-6, and `core/scroll.py`, `ui/starfield.py` and `ui/hud.py` must be in `game.apk`.

Integration checks for DRA-19, on top of the required browser checks and every DRA-5, DRA-6 and DRA-13 check above (all must still pass: DRA-19 changes no gameplay).
- **No `-0.00` in the overlay (`?debug=1`):** hold ArrowUp the whole time, so the ship sits on the top line and never falls to a respawn. While holding it, tap ArrowLeft for about 0.2 s, release it, wait about 3 s, and take a screenshot. The overlay's third line reads `vx 0.00`, not `vx -0.00`. Source: scope report DRA-19, Player sees; DRA-6-debug-overlay.md, Presentation.
- **Null character in debug mode (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change, only a stand-in from the command line. Before calling `run()`, replace `app.loop.start` with an async function that raises `ValueError("bad\x00value")`. The log shows the start line, then ERROR `unexpected error, showing the error screen` with the `ValueError` traceback, and no `error screen failed` line. The error screen is drawn and the process idles until it is stopped. Source: scope report DRA-19, item 4; this contract, Rules, Error guard.

## Impact
DRA-19 changes this frozen contract (v3). One guard rule changes: the debug-mode detail line also loses its null characters. Every file in `game/` that depends on it, found by grepping `game/` (tests included) for `guarded`, `_detail`, `detail`, `splitlines` and `draw_error_screen`:

| File | Change needed |
|---|---|
| `game/app/guard.py` | the debug-mode detail also drops every `\x00`, next to the newline handling. Normal mode still passes `None`. |
| `game/app/loop.py`, `game/app/frame.py`, `game/app/mode.py`, `game/app/log.py`, `game/app/settings.py` | none. |
| `game/main.py` | none. |
| `game/ui/error_screen.py` | none. It draws whatever `detail` it gets. |
| `game/tests/ui/test_error_screen.py` | none. It calls the view directly with its own strings. |
| `game/scripts/start-driftward-ace.sh`, `pygbag.ini` | none. |

All app changes are the Integration Engineer's, during DRA-19 integration. No task file.

## Rationale
- **`choose_mode` is pure and returns the rejected value.** The WARNING for a bad switch must go out after logging is configured, and logging needs the mode first. Returning the rejected value lets `run()` set up logging and then warn, with one config call.
- **`read_switch` runs before logging and outside the guard.** It only reads a string and has nothing to fail on in normal use. If it ever raises, Python prints the traceback to stdout. In the browser that is pygbag's hidden terminal, not the devtools console (D2), so the page stays blank. The same holds for the startup module imports and `setup_logging`. This gap is accepted because that code is stdlib only and small. The guard can't cover it, because the guard needs logging, and logging needs the mode.
- **Heavy imports inside the guard.** In round 0, pygame failed while `main.py` imported `app.loop`, before the guard or logging existed. The page stayed blank and the console was empty. So the startup modules import only the stdlib, and everything that can realistically fail at import (pygame, `ui`, later `core` and assets) is first imported by `start()` inside the guard. `app.frame` is a separate module so that `app.loop` stays light and the loop code itself still imports pygame at the top, as usual.
- **The guard imports its error screen late, and opens a window if there is none.** An import error in `app.frame` happens before `pygame.init()`, so there is no surface yet. Opening one in the guard lets that error still show the error screen. If pygame itself is missing, the error screen can't be shown at all, so the guard logs a second traceback and returns instead of idling. Idling would need pygame's event queue and would hang.
- **`app/settings.py` holds `TICK_RATE`.** It is a constants-only module with no imports. In DRA-5 it also held `SCREEN_SIZE`, so the guard could read it without pygame. From DRA-6, see the next point.
- **The screen size moved to `core/world.py` (DRA-6).** Core needs the walls and the floor, and core may never import `app`. Keeping a copy in `app/settings.py` would leave two homes for one guess value. The guard may not import `core` at module level (import boundary), so it imports `core.world` inside its error step, next to pygame and `ui.error_screen`. `core/world.py` is constants only, so that import can't realistically fail.
- **The release package is set in `pygbag.ini`.** pygbag packs the whole `game/` folder by default, so tests and tooling shipped in round 1. `pygbag.ini` is pygbag 0.9.3's own way to exclude them, with no flag or template change. It is a build file read on the build machine, not a runtime file, so it may sit at the repo root.
- **The error screen takes `detail`, not the mode.** game/CONTEXT.md says only `game/app/` and the debug overlay read the run mode. The guard decides normal or debug content, and the view only draws what it's given. The cut to screen width stays in the view, because only the view knows the font metrics.
- **`ui/look.py` holds `BACKGROUND`.** placeholder_bg is a look value, used by the loop's fill and by the error screen. One home in code avoids two copies of a guess value drifting apart.
- **`TICK_RATE` stays in `game/app/`.** `core.ship.step` is one tick by definition and never needs the rate. Only the loop turns frame time into ticks.
- **The mode reaches `frame_loop` through `functools.partial`.** `guarded` awaits a body with no arguments, and the loop needs the mode only to set `overlay_visible` and to gate F3. `guarded` keeps its DRA-5 signature.
- **Held keys come from `pygame.key.get_pressed()`, read once per frame.** That is SDL's own key state, so a missed event can't leave a key stuck in a set of our own. Reading it once per frame gives every tick in that frame the same thrust, so a frame with several ticks behaves like several frames with one tick.
- **Key lines log the ship before this frame's ticks.** That is the state the player saw when the key went down or up. The integration check needs only that y changes between the two lines.
- **Ship events are logged in core, key events in the app.** Each side logs what only it knows: the app sees the key events, core sees the wall, the line and the floor. Core logging is by event and doesn't change any rule, so core still behaves the same in both modes.
- **F3 lives in the app.** It is input, and only the app reads input. The overlay view never sees the mode or the key, only whether the app calls it.
- **The catch-up cap drops time instead of saving it.** The Director chose 5 ticks per frame, with owed time beyond that dropped (decision-log row 21). Without it, a long hidden-tab gap would run every missed tick in one frame: the ship would jump ahead unseen, and a slow frame could snowball. Setting the accumulator to 0.0 is the plain reading of "dropped". The fraction of a tick it also drops is under 1/60 s and can't be seen.
- **The cap is in `app/settings.py`, not core.** It is about frames, and only the loop knows about frames. Core sees only whole ticks, so the rules stay the same whatever the frame rate.
- **The scroll starts right after the spawn (DRA-13).** The control card doesn't exist yet, so the Director set play start to the moment the ship first appears at screen center. Calling `start_scroll()` next to `spawn()`, before the first frame, makes tick 0 the state the first frame shows.
- **Dropped catch-up time doesn't scroll (DRA-13).** Distance counts ticks the game ran. Time the cap drops is never run, so the world doesn't jump ahead after a hidden tab, the same as the ship.
- **The HUD is drawn last (DRA-13).** 10-ui.md, rule 1 puts the HUD on top of everything. The overlay and the HUD never overlap, so moving the overlay from last to second-to-last changes no pixel today.
- **The cap logs only when it starts.** A slow device can hit the cap every frame. Logging each time would be a line per frame, which the log policy forbids.
- **Browser logs go to `console.log`.** In pygbag 0.9.3, stdout and stderr reach only its hidden terminal, never the devtools console. Writing through `platform.window.console.log` makes the start line visible, as the scope report promises. Every level uses `console.log`, not `console.warn` or `console.error`, as the Director decided (D2). Desktop keeps stdout, so the level is still readable from the line text.
- **The PEP 723 block in `main.py`.** pygbag reads only `main.py` to pick the packages it installs. `main.py` imports only `asyncio` and `app.loop`, so the block is what gets pygame-ce into the browser build (D1). It is metadata only, with no logic and no import, so `main.py` stays a thin entry point.
- **The guard removes null characters, the view doesn't (DRA-19).** pygame's font render raises on a string with `\x00` in it. Before DRA-19 that made the guard log "error screen failed" and leave the last frame up, so a debug-mode player saw no error screen for that message. The guard already shapes `detail` into one line, so it is the one place that turns an exception into displayable text. Removing the character, not replacing it, keeps the rest of the message as it was. The full message with the null stays in the logged traceback (10-ui.md, error_debug_line).
- **Idle after the error, don't exit.** Ending `run()` hands control back to pygbag in a state we haven't tested. Idling keeps the canvas showing the error screen and keeps the page responsive.
- **The error screen is tested headless.** A browser run can't trigger an unexpected error without a debug-only trigger, and that would be new scope. Task DRA-5-02 proves the screen draws right in both modes.
- **Run-mode parsing has no permanent test.** It lives in `game/app/`, and `game/tests/check.sh` runs only `tests/core` and `tests/ui`. Only the Director can add an `app` step. The integration browser run covers the three cases (Rules, Integration checks, Run modes).
- **`?debug=1` and pygbag.** pygbag's page reads some URL parts for its own options. The Integration Engineer checks that `?debug=1` reaches Python unchanged and doesn't switch pygbag into a mode of its own. If it does, that is a blocked report: the switch value is locked in the GDD.
