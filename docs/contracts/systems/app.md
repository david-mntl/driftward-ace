# App base: entry point, logging, run mode, loop, error guard, error screen
Version: 10
Status: draft
Features: DRA-5, DRA-6, DRA-13, DRA-19, DRA-23, DRA-29, DRA-39, DRA-47, DRA-56, DRA-61, DRA-62
Created by: architect

## Purpose
Start the game, set up logging once, read the run mode once, run the async loop on the fixed 60 Hz tick, and catch any unexpected error so the page shows the error screen instead of freezing. That includes an error raised while importing pygame, core, the views or the frame loop. Build a release package that holds only runtime files.

Before the first frame the app loads and checks the tuning files once (the drifter files, the playtest switches and the shared hazard values) in both modes, and the debug test spawn list in debug mode only, and hands the checked values to core. It holds one `Run` (`docs/contracts/systems/run.md`). Play starts when the ship first appears. Each tick it calls `step_run` once; core does the ship, the scroll, the drifters, the lives, the respawn wait, game over and retry. In debug mode only, after each tick it hands the run the drifters the spawn list says are due, through `core.run.add_drifters`. Normal mode spawns nothing yet.

Each frame draws the starfield, the drifters (entry warnings, meteorites, satellites, chain lightnings, fireballs and coins) behind the ship, the coins' points popups over the drifters and behind the ship, the ship while `run.ship_visible` (the blink), in debug mode the hitbox and graze outlines, drifter labels and the debug overlay (F3 toggles them), the Game Over box with the final score while `run.game_over`, and the HUD with SCORE and the hearts on top. The arrow-key log lines carry the ship's x and y. The guard removes null characters from the debug-mode detail line, so an error message holding one still shows the error screen. Source: scope reports DRA-5 to DRA-47; `docs/contracts/systems/drifters.md`.

Who builds what:
- `game/main.py`, `game/app/`, `game/scripts/`, `pygbag.ini` (repo root): the Integration Engineer, during integration, from this contract. No task file.
- `game/ui/look.py`, `game/ui/error_screen.py`: the UI Developer, task `DRA-5-01-ui-developer`.
- `game/tests/ui/test_error_screen.py`: the QA Engineer, task `DRA-5-02-qa-engineer`.
- `game/core/world.py`, `game/core/ship.py`: DRA-6, see `docs/contracts/systems/world.md` and `docs/contracts/systems/ship.md`. Core is the same in both modes.
- `game/ui/ship_view.py`, `game/ui/debug_overlay.py`: DRA-6, see `docs/contracts/systems/ship.md` and `docs/contracts/systems/debug-overlay.md`.
- `game/core/scroll.py`, `game/ui/starfield.py`: DRA-13, see `docs/contracts/systems/scroll.md`.
- `game/ui/hud.py`: DRA-13, see `docs/contracts/systems/hud.md`. `game/ui/score_text.py`: DRA-61, same contract.
- `game/core/run.py`, `game/ui/game_over.py`: DRA-23, see `docs/contracts/systems/run.md`.
- `game/core/collision.py`, `game/core/levels.py`, `game/core/drifters/`, `game/ui/shapes.py`, `game/ui/drifters/`: DRA-29 and DRA-39, see `docs/contracts/systems/drifters.md`.
- `game/app/tuning.py`, `game/app/debug_spawns.py`: the Integration Engineer, during DRA-29 integration, from this contract. The hazards file, the satellite's own fields and the editable spawn list: during DRA-39 integration. The chain lightning's file and `telegraph_min`: during DRA-47 integration. The fireball's file and spawn rows with no position: during DRA-56 integration. The coin's file and drawing the popups: during DRA-62 integration. No task file.
- `game/ui/popup_view.py`: DRA-62, see `docs/contracts/systems/run.md`. `game/core/popup.py`, `game/core/drifters/coin.py`, `game/ui/drifters/coin_view.py`: DRA-62, see `systems/run.md` and `systems/drifters.md`.
- The data files are content, filled to their schemas by whoever the Director names (DRA-29: the main session, by Director decision): `game/tuning/drifters/meteorite.json` (`docs/contracts/schemas/drifter-tuning.schema.json`), `game/tuning/drifters/satellite.json` (`satellite-tuning.schema.json`), `game/tuning/drifters/chain_lightning.json` (`chain-lightning-tuning.schema.json`, DRA-47), `game/tuning/drifters/fireball.json` (`fireball-tuning.schema.json`, DRA-56), `game/tuning/drifters/coin.json` (`coin-tuning.schema.json`, DRA-62), `game/tuning/playtest.json` (`playtest-switches.schema.json`), `game/tuning/hazards.json` (`hazards.schema.json`) and `game/tuning/debug_spawns.json` (`debug-spawn-list.schema.json`), all schemas in `docs/contracts/schemas/`.

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
    FR --> CR["core.run"]
    FR --> UL["ui.look"]
    FR --> SF["ui.starfield"]
    FR --> SV["ui.ship_view"]
    FR --> DO["ui.debug_overlay"]
    FR --> GO["ui.game_over"]
    FR --> HU["ui.hud"]
    FR --> TU["app.tuning (DRA-29)"]
    FR --> DS["app.debug_spawns (DRA-29)"]
    FR --> UO["ui.drifters.registry (DRA-29)"]
    TU --> CO["core.drifters (DRA-29)"]
    DS --> CO
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
  T -- yes --> TK["one tick:<br/>run = step_run(run, thrust)<br/>debug mode: run = add_drifters(run,<br/>debug_spawns_due(spawn_list, run.scroll.ticks), tuning)"] --> T
  T -- no --> CAP{"acc still >= 1/60 s?"}
  CAP -- yes --> DROP["acc = 0<br/>(owed time dropped)"] --> D
  CAP -- no --> D["draw: fill ui.look.BACKGROUND,<br/>draw_starfield, render_drifter for each drifter,<br/>draw_points_popup for each popup (DRA-62),<br/>draw_ship if run.ship_visible,<br/>draw_debug_hitboxes and draw_debug_overlay if overlay_visible,<br/>draw_game_over(surface) then draw_final_score(surface, run.score)<br/>if run.game_over, then draw_hud"]
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
    rejected: (
        str | None
    )  # the switch value that was present but not "1"; None otherwise


def read_switch() -> str | None:
    ...
    # Browser (sys.platform == "emscripten"): the first value of URL query parameter `debug`.
    # Desktop: environment variable DRIFTWARD_DEBUG.
    # None when the switch is absent. Present with an empty value returns "".


def choose_mode(raw: str | None) -> ModeChoice:
    ...
    # Pure. No logging, no I/O.
```

### game/app/log.py (Integration Engineer)
```python
def setup_logging(mode: RunMode) -> None:
    ...
    # The only place that configures logging. Called once, at startup.
    # Installs exactly one handler on the root logger:
    #   browser (sys.platform == "emscripten"): writes each formatted line
    #     with platform.window.console.log
    #   desktop: logging.StreamHandler(sys.stdout)
```

### game/app/guard.py (Integration Engineer)
```python
async def guarded(body: Callable[[], Awaitable[None]], mode: RunMode) -> None:
    ...
    # Awaits body(). Holds the project's only `except Exception`.
    # Module level: stdlib and app.mode only. pygame, core.world and
    # ui.error_screen are imported inside the error step, never at the top.
```

### game/app/settings.py (Integration Engineer)
```python
TICK_RATE: int = 60  # 15-tech-constraints.md, tick_rate
MAX_TICKS_PER_FRAME: int = 5  # 15-tech-constraints.md, max_ticks_per_frame (guess)
```
Constants only. No imports. From DRA-6 the screen size lives in `core/world.py` (`SCREEN_W`, `SCREEN_H`), and `SCREEN_SIZE` is removed from here. See Impact.

### game/app/loop.py (Integration Engineer)
```python
async def run() -> None:
    ...
    # Startup order, then guarded(functools.partial(start, choice.mode), choice.mode).


async def start(mode: RunMode) -> None:
    ...
    # The guarded body. Imports app.frame here, inside the guard, then awaits frame_loop(mode).
```
Module level: stdlib, `app.mode`, `app.log` and `app.guard` only. No pygame, no `core`, no `ui`, no `app.frame`.

### game/app/frame.py (Integration Engineer)
```python
ARROW_NAMES: dict[
    int, str
]  # pygame.K_UP -> "up", K_DOWN -> "down", K_LEFT -> "left", K_RIGHT -> "right"


async def frame_loop(mode: RunMode) -> None:
    ...
    # pygame init, window, frames until pygame.QUIT.
    # Owns: run (core.run.Run), thrust (core.ship.Thrust), overlay_visible (bool).
```
Imports pygame, `app.settings`, `app.mode`, `app.tuning` and `app.debug_spawns` (DRA-29), `core.world`, `core.ship` (for `Thrust`), `core.run`, `ui.look`, `ui.starfield`, `ui.drifters.registry` (DRA-29, for `render_drifter`), `ui.ship_view`, `ui.debug_overlay`, `ui.game_over` and `ui.hud`. From DRA-23 it no longer imports `core.scroll`, `spawn` or `step`. Only `start()` imports this module, inside the guard.

App-owned state in `frame_loop` (DRA-23, DRA-29, DRA-39):
```python
tuning: DrifterTuning  # DRA-29. app.tuning.load_tuning() once, before start_run(). Never reloaded
spawn_list: (
    DebugSpawnList | None
)  # DRA-39. Debug mode: app.debug_spawns.load_debug_spawns(tuning) once,
# right after load_tuning(). Normal mode: None, the file is never read
run: Run  # core.run.start_run() before the first frame; replaced by step_run() every tick,
# and by add_drifters() after a tick in debug mode
thrust: Thrust  # rebuilt once per frame from the held arrow keys
overlay_visible: (
    bool  # True from the first frame in debug mode, always False in normal mode.
)
# F3 flips it, debug mode only.
```
The ship, the scroll and the drifters are `run.ship`, `run.scroll` and `run.drifters`. The app never keeps its own copy.

### game/app/tuning.py (Integration Engineer, DRA-29)
```python
TUNING_DIR: (
    Path  # the game's tuning folder: Path(__file__).resolve().parent.parent / "tuning"
)
PLAYTEST_FILE: str = "playtest.json"  # in TUNING_DIR
HAZARDS_FILE: str = "hazards.json"  # in TUNING_DIR. DRA-39
DRIFTERS_DIR: str = (
    "drifters"  # in TUNING_DIR; one "<drifter_type value>.json" per DrifterType
)


def load_tuning() -> DrifterTuning:
    ...
    # Reads and checks the playtest switches, the shared hazard values (DRA-39) and one file per
    # DrifterType, then builds the core dataclasses (docs/contracts/systems/drifters.md, Interface,
    # core/drifters/tuning.py, SatelliteVariantExtra in core/drifters/satellite.py, and from DRA-47
    # ChainLayout, ChainLightningVariantExtra and ChainLightningTypeExtra in core/drifters/chain_lightning.py,
    # from DRA-56 FireballTypeExtra and fireball_hitbox in core/drifters/fireball.py,
    # and from DRA-62 CoinVariantExtra, CoinTypeExtra and coin_hitbox in core/drifters/coin.py).
    # Reads the module-level TUNING_DIR at call time. Raises on any bad file.
```
Not a startup module: it imports `core.drifters`, so only `app.frame` imports it, inside the guard.

### game/app/debug_spawns.py (Integration Engineer, DRA-29; editable list DRA-39)
The debug test spawn list, a file the Director edits by hand: `game/tuning/debug_spawns.json`, to `docs/contracts/schemas/debug-spawn-list.schema.json`. A temporary stand-in kept in the scope reports, not in the GDD. Debug mode only.
```python
SPAWN_LIST_FILE: str = (
    "debug_spawns.json"  # in app.tuning.TUNING_DIR, read at call time
)
ALL_ROWS: str = "all"  # the mode that plays every row
DEFAULT_MODE: str = (
    ALL_ROWS  # scope report DRA-39, Values needed (stand-in): mode left out
)
DEFAULT_LOOP_TICKS: int = (
    180  # scope report DRA-39, Values needed (stand-in, kept from DRA-29):
)
# loop_ticks left out. 3 s


@dataclass(frozen=True, slots=True)
class DebugSpawnList:
    """The checked list, ready to play."""

    mode: str  # "all" or a DrifterType value
    loop_ticks: int  # ticks, >= 1
    schedule: tuple[
        tuple[int, Placement], ...
    ]  # (offset within the loop, placement) for each row in
    # play, in file order. Offsets from 0 to loop_ticks - 1


def load_debug_spawns(tuning: DrifterTuning) -> DebugSpawnList:
    ...
    # Reads and checks the file, then every row by spawning it once with spawn_drifter(placement, 1,
    # tuning). Builds the schedule for the rows in play. Raises on any problem.


def debug_spawns_due(spawn_list: DebugSpawnList, ticks: int) -> tuple[Placement, ...]:
    ...
    # () when ticks < 1. Otherwise every placement in the schedule whose offset ==
    # (ticks - 1) % spawn_list.loop_ticks, in schedule order.
    # ticks is run.scroll.ticks after the tick: 1 on the first tick of play.
```
Not a startup module: it imports `core.drifters`. DRA-39 removes `DEBUG_SPAWN_PERIOD` and `DEBUG_SPAWNS`; their three meteorite rows move into the file.

### pygbag.ini (repo root, Integration Engineer)
```ini
[DEPENDENCIES]
ignoreDirs = [...]    # folders under game/ left out of the package
ignoreFiles = [...]   # files under game/ left out of the package
```
pygbag 0.9.3 reads it from its working directory. The start script and the build check both run pygbag from the repo root. Source: Director decision (DRA-5 close-out, round 1 observations). docs/crew/roster.md, row 12.

The DRA-6 and DRA-13 call blocks below are kept as history. From DRA-23 the ship and scroll calls in them are replaced: the current order is the DRA-23 block after them.

DRA-6 calls, all made by `frame_loop`. Their signatures are set in the DRA-6 contracts:
```python
# before the first frame:
ship = spawn()  # systems/ship.md
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
ship = step(ship, thrust)  # systems/ship.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_ship(surface, ship)  # systems/ship.md
if overlay_visible:
    draw_debug_overlay(surface, ship)  # systems/debug-overlay.md
```

DRA-13 calls, all made by `frame_loop`. Their signatures are set in the DRA-13 contracts. The full order, with the DRA-6 calls in place:
```python
# before the first frame:
ship = spawn()
scroll = start_scroll()  # systems/scroll.md, right after spawn(): play starts
# per tick, inside the accumulator loop:
ship = step(ship, thrust)
scroll = step_scroll(scroll)  # systems/scroll.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, scroll)  # systems/scroll.md, behind everything
draw_ship(surface, ship)
if overlay_visible:
    draw_debug_overlay(surface, ship)
draw_hud(
    surface, scroll, below_overlay=debug
)  # systems/hud.md, last; debug = mode is RunMode.DEBUG
```

DRA-23 calls, all made by `frame_loop`. Their signatures are set in `systems/run.md` and `systems/hud.md`. They replace the DRA-6 and DRA-13 ship and scroll calls above. The full order:
```python
# before the first frame:
run = start_run()  # systems/run.md: spawn() and start_scroll(), play starts
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
run = step_run(run, thrust)  # systems/run.md: the only call per tick
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, run.scroll)
if run.ship_visible:
    draw_ship(surface, run.ship)  # the blink
if overlay_visible:
    draw_debug_overlay(surface, run.ship)
if run.game_over:
    draw_game_over(surface)  # systems/run.md, Presentation
draw_hud(surface, run, below_overlay=debug)  # systems/hud.md, last
```

DRA-29 calls, all made by `frame_loop`. Their signatures are set in `systems/drifters.md`, `systems/run.md` and `systems/debug-overlay.md`. They add to the DRA-23 block above. The full order:
```python
# before the first frame:
tuning = load_tuning()  # app.tuning, both modes. A bad file raises here
run = start_run()
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
run = step_run(run, thrust)
if debug:
    run = add_drifters(
        run, debug_spawns_due(run.scroll.ticks), tuning
    )  # systems/run.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, run.scroll)
for obj in run.drifters:
    render_drifter(surface, obj)  # systems/drifters.md: warnings and drifters
if run.ship_visible:
    draw_ship(surface, run.ship)  # the inverted T (systems/ship.md)
if overlay_visible:
    draw_debug_hitboxes(
        surface, run
    )  # systems/debug-overlay.md: outlines and labels first
    draw_debug_overlay(surface, run.ship)
if run.game_over:
    draw_game_over(surface)
draw_hud(surface, run, below_overlay=debug)
```

DRA-39 calls, all made by `frame_loop`. They change the DRA-29 block above only before the first frame and in the tick. The draw order is unchanged: `render_drifter(surface, obj)` keeps its signature (the brightness and the tilt come from the drifter itself).
```python
# before the first frame:
tuning = (
    load_tuning()
)  # app.tuning, both modes: drifter files, playtest.json, hazards.json
spawn_list = (
    load_debug_spawns(tuning) if debug else None
)  # app.debug_spawns, debug mode only
run = start_run()
# per tick, inside the accumulator loop:
run = step_run(run, thrust)
if debug:
    run = add_drifters(run, debug_spawns_due(spawn_list, run.scroll.ticks), tuning)
```

DRA-61 calls. They add one call to the DRA-29 draw block above: the final score line, right after the Game Over box. Its signature is set in `systems/run.md`. `draw_game_over(surface)` and `draw_hud(surface, run, below_overlay=debug)` don't change; the HUD reads `run.score` itself.
```python
# per frame, draw:
if run.game_over:
    draw_game_over(surface)  # systems/run.md, Presentation: box, title, prompt
    draw_final_score(surface, run.score)  # systems/run.md, Presentation: the score line
draw_hud(surface, run, below_overlay=debug)  # systems/hud.md, last
```
`app/frame.py` imports `draw_final_score` from `ui.game_over`, next to `draw_game_over`.

DRA-62 calls. They add one loop to the DRA-29 draw block above: the points popups, right after the drifters and before the ship. Its signature is set in `systems/run.md`. Nothing else in the frame changes: coins enter through the same `add_drifters` call and are drawn by `render_drifter`.
```python
# per frame, draw:
for obj in run.drifters:
    render_drifter(surface, obj)  # systems/drifters.md: coins too
for popup in run.popups:
    draw_points_popup(surface, popup)  # systems/run.md, Presentation: over the drifters
if run.ship_visible:
    draw_ship(surface, run.ship)  # the ship stays on top of the popups
```
`app/frame.py` imports `draw_points_popup` from `ui.popup_view`.

### game/ui/look.py (UI Developer)
```python
BACKGROUND: tuple[int, int, int]  # 12-art-and-audio.md, placeholder_bg
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
The app draws nothing itself beyond the background fill. The ship view and the debug overlay have their own Presentation sections in `docs/contracts/systems/ship.md` and `docs/contracts/systems/debug-overlay.md`. The starfield and the HUD have theirs in `docs/contracts/systems/scroll.md` and `docs/contracts/systems/hud.md`. The blink and the Game Over box have theirs in `docs/contracts/systems/run.md` (DRA-23). The drifters and their entry warnings have theirs in `docs/contracts/systems/drifters.md` (DRA-29). The error screen reads no core state, only what the guard passes it.

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
- Inside the guard: `pygame.init()`, then `pygame.display.set_mode((SCREEN_W, SCREEN_H))` from `core.world`. Source: 03-world-and-camera.md, screen_w, screen_h (guess). systems/world.md.
- Before the first frame (DRA-29): `tuning = load_tuning()`, in both modes, before `start_run()`. A bad or missing tuning file raises inside the guard, so the page shows the error screen and the log holds the file and field. Source: game/CONTEXT.md, Error handling (validate at the edge); 15-tech-constraints.md, rule 8; scope report DRA-29, Limits ("The app loads and validates them once at startup").
- Before the first frame, debug mode only (DRA-39): `spawn_list = load_debug_spawns(tuning)`, right after `load_tuning()`. A bad or missing list raises inside the guard the same way. Normal mode never reads the file, so a broken list can't break normal play. Source: 15-tech-constraints.md, rule 7 (debug only adds the test spawn list); scope report DRA-39, Limits.
- Before the first frame: `run = start_run()`, and `overlay_visible = mode is RunMode.DEBUG`. Play starts here: the ship first appears at screen center on the first frame drawn after this. Source: 03-world-and-camera.md, ship_start; 10-ui.md, debug_overlay_toggle (shown from the first frame); scope report DRA-13, Values needed (play start); systems/run.md (DRA-23).
- The app never calls `spawn`, `step`, `start_scroll` or `step_scroll` itself, and never calls `start_run()` again. A respawn, the wait, game over and a retry all happen inside `step_run`. Source: systems/run.md (DRA-23).
- **Game over.** While `run.game_over` is True the frame loop carries on as always: it reads events, builds `thrust`, runs ticks (`step_run` keeps the run frozen and watches for the retry) and draws. Nothing in the app changes. Source: 02-game-flow.md, rules 5 and 6; systems/run.md.
- Each frame, in order: read all events, build `thrust` from the held keys, add the frame time to the accumulator, run one tick per whole 1/60 s in the accumulator, draw, `pygame.display.flip()`, `await asyncio.sleep(0)`. Source: 15-tech-constraints.md, rules 1 and 2.
- Frame time comes from a monotonic clock (`time.perf_counter`). Ticks never use frame time. Source: 15-tech-constraints.md, rule 2.
- **Held keys.** After the events, read `pygame.key.get_pressed()` once and build `Thrust(up=pressed[K_UP], down=pressed[K_DOWN], left=pressed[K_LEFT], right=pressed[K_RIGHT])`. Every tick in that frame uses the same `thrust`. Only the four arrow keys move the ship. Source: 01-vision.md, locked decision 1; 04-ship.md, rule 2.1.
- **Tick.** `run = step_run(run, thrust)`. One `step_run` call per tick. In debug mode only, right after it: `run = add_drifters(run, debug_spawns_due(spawn_list, run.scroll.ticks), tuning)`. In normal mode nothing is added. The app never builds a drifter itself and never changes `run.drifters`. Source: 04-ship.md, rule 1; 15-tech-constraints.md, rules 2 and 7; systems/run.md; scope report DRA-29, Limits ("Normal mode spawns nothing yet").
- **Draw.** In this order: fill with `ui.look.BACKGROUND`; `draw_starfield(surface, run.scroll)`; `render_drifter(surface, obj)` for each `obj` in `run.drifters`, in order (DRA-29); `draw_points_popup(surface, popup)` for each `popup` in `run.popups`, in order (DRA-62); `draw_ship(surface, run.ship)` only if `run.ship_visible`; only if `overlay_visible`, `draw_debug_hitboxes(surface, run)` (DRA-29) then `draw_debug_overlay(surface, run.ship)`; only if `run.game_over`, `draw_game_over(surface)` then `draw_final_score(surface, run.score)` (DRA-61: the final score); `draw_hud(surface, run, below_overlay=debug)` last, on top of everything. Source: systems/ship.md, systems/drifters.md, systems/debug-overlay.md, systems/scroll.md, systems/run.md and systems/hud.md, Presentation; 10-ui.md, rules 1 (the HUD on top) and 3 (the blink); 12-art-and-audio.md, rule 2 (the background stays behind).
- **Drifters behind the ship (DRA-29).** Warnings and meteorites are drawn after the starfield and before the ship, so the player's ship stays on top where they cross.
- **Popups over the drifters (DRA-62).** The points popups are drawn after every drifter, so they show over the other drifters, by Director decision, and before the ship, which stays on top as it does over every drifter. Source: scope report DRA-62, Limits and Decision log (Q5, Director override of Objection 1); systems/run.md, Presentation.
- **`below_overlay`** is `mode is RunMode.DEBUG`, fixed for the run. Never `overlay_visible`: in debug mode the HUD stays below the overlay's place while F3 hides it, so the readout never jumps. Source: scope report DRA-13, HUD layout.
- `pygame.QUIT`: log INFO `quit` and leave the loop. That only happens on desktop.
- **Arrow keys** (Up, Down, Left, Right): on `KEYDOWN` log DEBUG `key down key=%s x=%.2f y=%.2f`, on `KEYUP` log DEBUG `key up key=%s x=%.2f y=%.2f`, with names `up`, `down`, `left`, `right` and the ship's `x` and `y` (`run.ship.x`, `run.ship.y` from DRA-23) at the moment the event is read (before this frame's ticks). Example: `key down key=up x=320.00 y=240.00`. No other arrow event is logged. Source: game/CONTEXT.md, Logging (a key pressed or released is an event). 01-vision.md, locked decision 1. Director decision (DRA-6: the integration check compares y between key-down and key-up).
- **F3.** In debug mode, on `KEYDOWN` of `pygame.K_F3`: flip `overlay_visible` and log DEBUG `overlay visible=%s`. `KEYUP` of F3 does nothing. In normal mode F3 does nothing and logs nothing. F3 never retries: only `thrust`, built from the four arrows, reaches `step_run` (02-game-flow.md, retry_key, locked). Source: 10-ui.md, debug_overlay_toggle (guess) and rule 7.
- **Log by event.** The frame loop logs only on the events in these rules: quit, arrow keys, F3 and the cap. Never a line per tick or per frame. Ship events (wall hit, top-line stop) are logged by `core.ship`, the scroll start by `core.scroll`, and the run's events (life lost, respawn, wait end, invulnerable end, game over, new run, and from DRA-29 drifter spawn, active, touch and gone) by `core.run`, not by the app. The app's only drifter lines are the one `tuning loaded` line at startup and, in debug mode, the one `debug spawns loaded` line after it (DRA-39). Source for the run's lines: systems/run.md, Logging (DRA-23). Source: 15-tech-constraints.md, rule 9; systems/ship.md, Rules, Logging.
- **Catch-up cap.** One frame runs at most `MAX_TICKS_PER_FRAME` (5) ticks. If, after the 5th tick, the accumulator still holds one tick or more, set it to 0.0: the owed time is dropped, never run later. The game carries on from where it was. Source: 15-tech-constraints.md, max_ticks_per_frame (guess) and rule 2; 91-decision-log.md, row 21.
- **Cap log, by event.** Log DEBUG `tick cap hit, dropped %.3f s` (the seconds dropped) on a frame where the cap drops time and the frame before didn't. While frames keep hitting the cap, log nothing more. The next capped frame after an uncapped one logs again. Source: 15-tech-constraints.md, rule 9.
- No `time.sleep`, no thread, no blocking call. Source: 15-tech-constraints.md, rule 1.

Tuning loader (`app/tuning.py`, DRA-29). Source: scope report DRA-29, Limits; game/CONTEXT.md, Error handling ("Validate at the edge ... raise with a message that says what was wrong and where"); CLAUDE.md, Rules for every agent (no silent schema drift):
- Reads `TUNING_DIR / PLAYTEST_FILE`, then `TUNING_DIR / HAZARDS_FILE` (DRA-39), then `TUNING_DIR / DRIFTERS_DIR / f"{drifter_type.value}.json"` for every `DrifterType`, in enum order. UTF-8, `json.loads`. Once, at startup. Read with plain `open`/`Path.read_text`: no blocking beyond a small local file, no network.
- Checks every rule of `docs/contracts/schemas/playtest-switches.schema.json`, `hazards.schema.json`, `drifter-tuning.schema.json`, `satellite-tuning.schema.json`, `chain-lightning-tuning.schema.json` (DRA-47), `fireball-tuning.schema.json` (DRA-56) and `coin-tuning.schema.json` (DRA-62) by hand (no schema library: pygbag has none). No unknown field; types exact. A number is an `int` or a `float`, never a `bool`. In the playtest and drifter files every field is required. `entry_warning_ticks` is an `int` ≥ 1. `speed_ratio` ≥ 0. `width`, `height`, `r`, `w`, `h` > 0. Variant names match `^[a-z][a-z0-9_]*$`, at least one variant, each with at least one shape.
- **Hazards file** (DRA-39). Every field optional; `{}` is valid. `rehit_cooldown` is an `int` ≥ 0 (never a `bool`); `rehit_dim` a number from 0 to 1; `telegraph_min` (DRA-47) an `int` ≥ 0 (never a `bool`). A field left out takes its default from `core.drifters.base` (`DEFAULT_REHIT_COOLDOWN_TICKS`, `DEFAULT_REHIT_DIM`, `DEFAULT_TELEGRAPH_MIN_TICKS`); the loader holds no copy of those numbers. The file itself must exist. Builds `HazardRules(rehit_cooldown_ticks=..., rehit_dim=..., telegraph_min_ticks=...)`. Source: scope report DRA-39, Limits; 05-lives-and-damage.md, Values; 07-drifters.md, telegraph_min.
- **The chain lightning's file** (DRA-47), `drifters/chain_lightning.json`, checked against `chain-lightning-tuning.schema.json` instead of `drifter-tuning.schema.json`. Every field is required. On top of the shared fields: `node_spacing`, `node_size`, `arc_width`, `ray_length` and `ray_width` numbers > 0; `charge_ticks`, `fire_ticks` and `charge_rays` `int`s ≥ 1 (never a `bool`); `entry_warning_icon` a variant name. Each variant has exactly `nodes`, `arcs` and `invert_mirror` (no `width`, `height` or `hitbox`): `nodes` a list of 2 or 3 points, each a list of exactly two numbers; `arcs` a list of at least one pair, each a list of exactly two `int`s ≥ 0; `invert_mirror` `"left_right"` or `"top_bottom"`. Then the rules the schema can't express: `default_variant` and `entry_warning_icon` are variant names; each arc names two different nodes that exist in its variant, and no two arcs of a variant join the same two nodes (in either order); each arc's two nodes are 1 unit apart (`abs(distance − 1) <= 1e-6`); the box around a variant's node points is centered on (0, 0) (`abs(center) <= 1e-6` on each axis); `arc_width <= node_size`. Errors name the field the same way, e.g. `tuning/drifters/chain_lightning.json: variants.trio_l.arcs[1] must join two nodes 1 unit apart`, `tuning/drifters/chain_lightning.json: entry_warning_icon must be one of the variant names`.
- **What the loader builds for the chain lightning** (DRA-47): for each variant, `layout = ChainLayout(nodes=(each point × node_spacing, as (x, y) floats), arcs=(each pair as a tuple), invert_mirror=InvertMirror(value))`, then `width, height = layout_size(layout.nodes, node_size)` and `VariantTuning(width=width, height=height, hitbox=chain_hitbox(layout.nodes, layout.arcs, node_size, arc_width), extra=ChainLightningVariantExtra(layout=layout))`; for the type, `DrifterTypeTuning(..., extra=ChainLightningTypeExtra(node_size=..., arc_width=..., charge_ticks=..., fire_ticks=..., charge_rays=..., ray_length=..., ray_width=..., warning_layout=<the layout of the entry_warning_icon variant>))`. All from `core.drifters.chain_lightning`, so the hitbox rule has one home. The footprint check of the other files is not run on these shapes: `arc_width <= node_size` already keeps every line inside its nodes, and lines are never read as boxes. The meteorite and the satellite get `extra=None` on their `DrifterTypeTuning`. Source: docs/contracts/systems/drifters.md, Rules, Chain lightning (Layout) and Tuning files.
- **The fireball's file** (DRA-56), `drifters/fireball.json`, checked against `fireball-tuning.schema.json` instead of `drifter-tuning.schema.json`. Every field is required: the shared `default_variant`, `variants`, `speed_ratio` and `entry_warning_ticks`, checked as for every drifter file, plus `angle_degrees`, a number ≥ 0 and < 90, and `tail_ratio`, a number > 0. Each variant has exactly `head_width`, a number > 0 (no `width`, `height` or `hitbox`). `default_variant` is one of the variant names. Errors name the field the same way, e.g. `tuning/drifters/fireball.json: tail_ratio must be a number > 0`, `tuning/drifters/fireball.json: variants.big.head_width must be a number > 0`.
- **What the loader builds for the fireball** (DRA-56): for each variant, `VariantTuning(width=head_width, height=head_width, hitbox=fireball_hitbox(head_width, tail_ratio, angle_degrees, False), extra=None)`; for the type, `DrifterTypeTuning(..., extra=FireballTypeExtra(angle_degrees=..., tail_ratio=...))`. Both from `core.drifters.fireball`, so the hitbox rule has one home. The footprint check of the other files is not run on these shapes: the tail lies outside the head's footprint by design (drifters/06-fireball.md, size and hitbox; 91-decision-log.md, rows 61 and 64), and rule 8 is kept because the fireball's look is exactly those two circles. Source: docs/contracts/systems/drifters.md, Rules, Fireball and Tuning files.
- **The coin's file** (DRA-62), `drifters/coin.json`, checked against `coin-tuning.schema.json` instead of `drifter-tuning.schema.json`. Every field is required. It has `default_variant` and `variants` like every drifter file, and no `speed_ratio` and no `entry_warning_ticks` (either one is an unknown field). Its own fields: `crystal_width`, `crystal_height`, `body_height`, `ring_width` and `ring_height`, each an `int` ≥ 2 and even (never a `bool`); `glint_size` an `int` ≥ 1; `glint_left` and `glint_top` `int`s ≥ 0; `popup_ticks` an `int` ≥ 1; `popup_rise_per_tick` a number ≥ 0. Each variant has exactly `points`, an `int` ≥ 1, and `glint`, a boolean. Then the rules the schema can't express: `default_variant` is a variant name; `body_height < crystal_height`; the glint lies inside the crystal's box: `glint_left + glint_size <= crystal_width` and `glint_top + glint_size <= crystal_height`. Errors name the field the same way, e.g. `tuning/drifters/coin.json: popup_ticks must be an integer >= 1`, `tuning/drifters/coin.json: variants.rare.points must be an integer >= 1`, `tuning/drifters/coin.json: crystal_width must be an even integer >= 2`.
- **What the loader builds for the coin** (DRA-62): for each variant, `VariantTuning(width=float(crystal_width), height=float(crystal_height), hitbox=coin_hitbox(crystal_width, body_height), extra=CoinVariantExtra(points=..., glint=...))`; for the type, `DrifterTypeTuning(variants=..., default_variant=..., speed_ratio=0.0, entry_warning_ticks=0, extra=CoinTypeExtra(body_height=..., ring_width=..., ring_height=..., glint_size=..., glint_left=..., glint_top=..., popup_ticks=..., popup_rise_per_tick=...))`. `coin_hitbox`, `CoinVariantExtra` and `CoinTypeExtra` come from `core.drifters.coin`, so the hitbox rule has one home. The two zeros are not tuning values: the spawner never reads `speed_ratio` for a parked drifter, and the coin is born ACTIVE with no warning (`systems/drifters.md`, Rules, Spawner and Coin). The footprint check runs on the coin's box as for every plain file and passes (12 × 10 inside 12 × 20). Source: `docs/contracts/systems/drifters.md`, Rules, Coin and Tuning files; scope report DRA-62, Limits ("Every value in the tuning file").
- **A drifter's own fields** (DRA-39). A drifter type with its own schema is checked against it instead of `drifter-tuning.schema.json`. The satellite: every variant also requires `angle_degrees`, a number ≥ 0 and < 90, and its `hitbox` is exactly two boxes. The loader builds `SatelliteVariantExtra(angle_degrees=...)` (`core.drifters.satellite`) into each `VariantTuning.extra`. The meteorite's variants have no `extra` (None). Error messages name the field the same way, e.g. `tuning/drifters/satellite.json: variants.angled.angle_degrees must be a number >= 0 and < 90`.
- Two rules the schema can't express, also checked: `default_variant` is one of the variant names; and every hitbox shape lies inside its variant's `width × height` footprint, centered on the drifter (circle: `|cx| + r <= width / 2` and `|cy| + r <= height / 2`; box: `|cx| + w / 2 <= width / 2` and `|cy| + h / 2 <= height / 2`). Source: 07-drifters.md, rule 8 (a hitbox is never bigger than what the player sees).
- On any problem: raise `ValueError` with the file and the field, the file named from the tuning folder down, e.g. `tuning/drifters/meteorite.json: variants.small.hitbox[0].r must be a number > 0`. Invalid JSON: `ValueError("tuning/playtest.json: not valid JSON: <decoder message>")`, raised `from` the decode error. A missing file: the `FileNotFoundError` rises as it is (it names the path). Never fall back to a default for a missing file. The guard shows the error screen.
- Builds `DrifterTuning(drifters={...}, switches=PlaytestSwitches(...), hazards=HazardRules(...))` with plain dicts, `Circle` and `Box` from `core.collision`. Core trusts these values.
- Extra files in `drifters/` that match no `DrifterType` are not read. Test task DRA-29-09 fails on them.
- Logs one INFO line after a good load: `tuning loaded drifters=%s hazard_speed_scaling=%s timer_scaling=%s rehit_cooldown=%d rehit_dim=%.2f telegraph_min=%d`, the drifter types as a comma-separated list of values, and the cooldown, dim and telegraph minimum in use (DRA-39 adds the cooldown and dim, DRA-47 the telegraph minimum). INFO because it is startup. Nothing else.

Debug test spawn list (`app/debug_spawns.py`). Source: scope report DRA-39, Feature, Limits and Values needed (temporary stand-ins, debug mode only, not in the GDD); 15-tech-constraints.md, rule 7; 91-decision-log.md, row 38:
- **File.** `app.tuning.TUNING_DIR / SPAWN_LIST_FILE` (`game/tuning/debug_spawns.json`), read once at startup in debug mode, UTF-8, `json.loads`. The Director edits it by hand; a change shows on the next page load.
- **Checks**, by hand, every rule of `docs/contracts/schemas/debug-spawn-list.schema.json`: `rows` required, a list (may be empty); `mode` and `loop_ticks` optional; no unknown field anywhere; types exact, never a `bool` for a number. Each row: `type` required; `x`, `y` optional numbers (DRA-56: a row may leave out both; the drifter decides what it needs); `variant` a string matching `^[a-z][a-z0-9_]*$`; `invert` a boolean; `speed` a number > 0. `loop_ticks` an `int` ≥ 1.
- **Checks the schema can't express.** `mode` is `"all"` or a `DrifterType` value. Each row's `type` is a `DrifterType` value. Then every row, in or out of play, is turned into a `Placement(drifter_type, x=..., y=..., variant=..., invert=..., speed=...)`, absent fields left at their `Placement` defaults, and spawned once with `spawn_drifter(placement, 1, tuning)`, and the result thrown away. Whatever that raises (a missing coordinate the drifter needs, an unknown variant, an invert the drifter lacks) is raised again as `ValueError` naming the row, e.g. `tuning/debug_spawns.json: rows[2]: satellite placement needs y`, `from` the original.
- **Errors** name the file and the field like the tuning loader: `tuning/debug_spawns.json: mode must be "all" or a drifter type (meteorite, satellite)`, `tuning/debug_spawns.json: rows[0].speed must be a number > 0`. Invalid JSON and a missing file as in the tuning loader. Never a default for a missing file.
- **Defaults.** `mode` left out: `DEFAULT_MODE`, `"all"`. `loop_ticks` left out: `DEFAULT_LOOP_TICKS`, 180. A row field left out: the drifter's default (`Placement`'s None or False). Source: scope report DRA-39, Values needed.
- **Rows in play.** With mode `"all"`, every row. With a drifter type, only the rows of that type. File order is kept.
- **Chain lightning rows** (DRA-47). `"type": "chain_lightning"` with `x` (required), and optionally `y`, `variant`, `invert` and `speed`; `"mode": "chain_lightning"` plays only those rows. No new code in this module: the type list, the mode check and the load-time spawn all go through `DrifterType` and `spawn_drifter`, so a chain lightning row without `x` fails with `chain_lightning placement needs x`. Its entry warning is settled by `add_drifters` in the run, not here. Source: scope report DRA-47, Limits.
- **Fireball rows** (DRA-56). `"type": "fireball"`, and optionally `x`, `y`, `variant`, `invert` and `speed`; `"mode": "fireball"` plays only those rows. The position picks the entry: neither `x` nor `y` is the default corner (top-left, or top-right with `invert`), `x` alone an entry along the top, `y` alone a side entry (the left wall, or the right with `invert`). So the loader no longer requires `x` or `y` in a row: that check moves to the drifter's own `start_position`, through the load-time spawn. A meteorite or chain lightning row without `x` still fails with `<type> placement needs x`, a satellite row without `y` with `satellite placement needs y`. `speed` is the Level 1 speed along the fireball's path; hazard speed × applies on top. No other new code: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. Source: scope report DRA-56, Limits and Not in GDD (speed).
- **Coin rows** (DRA-62). `"type": "coin"` with `x` (required) and optionally `y` and `variant`; `"mode": "coin"` plays only those rows. `x` alone starts it just above the top edge at that x; `x` and `y` place it at that spot, where it shows at once, with no warning. No new code in this module: the type list, the mode check and the load-time spawn go through `DrifterType` and `spawn_drifter`. So a coin row without `x` fails with `coin placement needs x`, one with `speed` with `coin has no speed`, and one with `invert: true` with `coin has no invert`, each named by its row as for every drifter. Source: scope report DRA-62, Limits ("coin rows set x and y, plus an optional variant. No speed. A coin-only mode") and Not in GDD (Director: "it shows position x and y"); 07-drifters.md, rule 14.
- **Timing.** The `n` rows in play are spread evenly over one loop: row `i` (from 0) has offset `(i × loop_ticks) // n`. `debug_spawns_due` places a row on every tick where `(run.scroll.ticks - 1) % loop_ticks` equals its offset. So the first row in play is placed on the first tick of play (`run.scroll.ticks == 1`), and the loop repeats every `loop_ticks` ticks. Rows that share an offset (more rows than ticks) are placed on the same tick, in file order. With the three DRA-29 meteorite rows in play and `loop_ticks` 180, they are placed on ticks 1, 61 and 121, then again from 181, exactly as in DRA-29. Source: scope report DRA-39, Feature ("The list loops"), Decision log (rows need only type and position); this contract, Rationale.
- The list counts the run's own ticks, so it freezes at game over and starts again with a retry.
- **Log.** One INFO line after a good load: `debug spawns loaded mode=%s rows=%d loop_ticks=%d`, with the number of rows in play. INFO because it is startup. Nothing else, and nothing per tick.
- Called only in debug mode. Never in normal mode. Game rules stay the same in both modes; the list only places drifters.
- Not a wave. No wave file, no wave clock, no wave picker. Waves replace it later. Source: scope report DRA-39, Out.

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
- The package (`game.apk` inside `game/build/web.zip`, and the live build the start script serves) holds only runtime files: `main.py`, `app/`, `ui/`, `core/`, and later the asset and data files the game reads. From DRA-6, `core/*.py` must be in it. From DRA-29, `tuning/` with its JSON files must be in it, along with the subpackages `core/drifters/` and `ui/drifters/`. Source: Director decision (DRA-5 close-out, round 1 observations).
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

Integration checks for DRA-6, on top of the required browser checks and every DRA-5 check above (all must still pass). Background, from DRA-23: with no key held, the ship falls off the floor once, about 1.07 s after play starts, loses a life, respawns at the center and waits there for an arrow press. Every later fall needs a press first, and the third fall ends the run with the Game Over box. Between checks, retry with a fresh arrow press (release every arrow, then press one) or open a fresh page. Before DRA-23 the ship respawned about once a second with no key held; the checks below that relied on it are reworded and marked (DRA-23).
- **Arrow keys with x/y (`?debug=1`):** hold ArrowUp for about 2 s (`keyboard.down`, wait, `keyboard.up`). The key-down and key-up lines both carry `x=` and `y=`. The key-up `y` is smaller than the key-down `y`, and after a 2 s hold it is `184.00` (top edge on the top line). Source: Director decision (DRA-5 integration, D3; DRA-6 design input).
- **Log by event, not by tick (`?debug=1`):** hold ArrowUp and ArrowLeft together for about 3 s. Between that key-down and key-up there is exactly one `top line stop` line and exactly one `wall hit side=left` line. (DRA-23) With the ship waiting at the respawn point and no key held for 5 s, the only new line is one `invulnerable end`, about 0.5 s after the respawn, never a line per tick. From DRA-13, the one `scroll start` line may also fall in that window if it covers the first 0.5 s of play. Source: 15-tech-constraints.md, rule 9; systems/ship.md and systems/run.md, Logging.
- **Respawn (`?debug=1`):** after the keys are released, a `respawn from x=... y=... wait=True` line appears within about 2 s, with `y` at least 496.00 (top edge at or past 480). (DRA-23) The line now comes from `core.run`, right after a `life lost lives=...` line. Source: DRA-6 scope report, Limits; systems/run.md, Logging.
- **Ship visible (`/`):** the canvas shows white (255, 255, 255) pixels (the ship) and no (0, 255, 0) pixels. F3 logs nothing and changes nothing. Source: systems/ship.md, Presentation; 10-ui.md, rule 7.
- **Overlay and F3 (`?debug=1`):** from the first frame there are (0, 255, 0) pixels on row 168, away from the ship. F3 logs `overlay visible=False` and those pixels go to the background color. F3 again logs `overlay visible=True` and they come back. Source: 10-ui.md, debug_overlay, debug_overlay_toggle.
- **Click to start, follow-up:** the Director asked for this again, because in DRA-5 headless Chromium skipped the click. Record, in a fresh tab: whether pygbag's click screen shows, whether "MEDIA USER ACTION REQUIRED" appears, `navigator.userActivation.hasBeenActive` before any click, the time of the start line, and whether `respawn` lines appear before the click (the ship already moving). Report what happened in Browser run, and under Observations only as the "How the browser checks are done" rules above say. A game that starts before the click doesn't fail DRA-6. A game that doesn't start after a click fails it. Source: Director decision (DRA-5 close-out, follow up; DRA-6 design input; DRA-19 close-out).
- **Catch-up cap (`?debug=1`):** hide the tab for about 5 s (see "How the browser checks are done" above), then let it run. One `tick cap hit, dropped ... s` line appears, with about the hidden time. It is not repeated every frame. The game carries on: the ship doesn't jump ahead by the hidden time, and the meters readout doesn't jump by the hidden time's distance. (DRA-23: before, this also checked that the respawn lines stayed about one a second. The ship now waits after a fall, so there is no steady respawn rate to check.) Source: 15-tech-constraints.md, max_ticks_per_frame, rules 2 and 9; Director decision (DRA-19 close-out).
- **Package contents:** as for DRA-5, and `core/world.py`, `core/ship.py`, `ui/ship_view.py` and `ui/debug_overlay.py` must be in `game.apk`.

Integration checks for DRA-13, on top of the required browser checks and every DRA-5 and DRA-6 check above (all must still pass). Background: 1.1 px a tick at 60 ticks a second is 66 px, so 6.6 m, a second. The readout gains about 66 m in 10 s.
- **Scroll start, logged once (`?debug=1`):** exactly one `scroll start tick=31` line after the start line. In about 10 s of play no second one appears, including across a fall, its `respawn from` line and the wait. (DRA-23) A retry starts a new run, and the new run logs its own `scroll start tick=31`. Source: systems/scroll.md, Rules, Logging; 03-world-and-camera.md, rule 4.
- **Readout counts up (`/`):** a screenshot right after play starts shows `0 m` at the top-left, with its text top near y 24. Screenshots about 5 s and 10 s later, with no key held (DRA-23: the ship falls once, then waits at the center), show larger whole numbers, the 10 s one about 66 m. Within a run the number never goes down. Source: scope report DRA-13, Player sees; systems/hud.md, Layout.
- **Hovering still earns meters (`/`):** hold ArrowUp for about 5 s so the ship sits on the top line. The readout keeps counting at the same rate as with no key held. Source: 03-world-and-camera.md, Edge cases.
- **Starfield moves (`/`):** the canvas has (90, 100, 140) pixels. Two screenshots about 1 s apart, after the first 0.5 s, show the dots about 66 px lower, with dots that left the bottom back at the top. In the first 0.5 s after play starts they sit still. Source: systems/scroll.md, Presentation.
- **No overlap in debug mode (`?debug=1`):** the four green overlay lines sit at the top-left, and the white readout sits below the last one, with a gap and no shared pixel row. Press F3: the overlay text goes away and the readout stays exactly where it was. F3 again brings the overlay back, still with no overlap. The overlay shows only x, y, vx and vy and its two lines, as in DRA-6. (DRA-23) The white hearts at the top right are not part of this check; read the top-left area only. Source: systems/hud.md, Rules; scope report DRA-13, Decision log.
- **Top line is still a ceiling (`?debug=1`):** the DRA-6 ArrowUp check still ends at `y=184.00`. Source: systems/ship.md, step 7.
- **Package contents:** as for DRA-6, and `core/scroll.py`, `ui/starfield.py` and `ui/hud.py` must be in `game.apk`.

Integration checks for DRA-19, on top of the required browser checks and every DRA-5, DRA-6 and DRA-13 check above (all must still pass: DRA-19 changes no gameplay).
- **No `-0.00` in the overlay (`?debug=1`):** hold ArrowUp the whole time, so the ship sits on the top line and never falls to a respawn. While holding it, tap ArrowLeft for about 0.2 s, release it, wait about 3 s, and take a screenshot. The overlay's third line reads `vx 0.00`, not `vx -0.00`. Source: scope report DRA-19, Player sees; systems/debug-overlay.md, Presentation.
- **Null character in debug mode (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change, only a stand-in from the command line. Before calling `run()`, replace `app.loop.start` with an async function that raises `ValueError("bad\x00value")`. The log shows the start line, then ERROR `unexpected error, showing the error screen` with the `ValueError` traceback, and no `error screen failed` line. The error screen is drawn and the process idles until it is stopped. Source: scope report DRA-19, item 4; this contract, Rules, Error guard.

Integration checks for DRA-23, on top of the required browser checks and every DRA-5, DRA-6, DRA-13 and DRA-19 check above, as reworded for DRA-23 (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: with no key held, the first fall comes on tick 64, about 1.07 s after play starts, from y 500.20. Positions are on the 640 × 480 canvas.
- **A fall costs a life (`?debug=1`, no key held):** about 1.07 s after play starts, `life lost lives=2`, then `respawn from x=320.00 y=500.20 wait=True`. Read the canvas after it: white heart pixels in the boxes at x 576 to 599 and x 608 to 631 (rows 8 to 31), and none in the box at x 544 to 567. Source: systems/run.md, Rules, step 5.2 and Logging; systems/hud.md, Presentation.
- **Three hearts at the start (`/`):** the first frames show white heart pixels in all three boxes, x 544 to 567, 576 to 599 and 608 to 631, rows 8 to 31, and no white pixel elsewhere in the area x 536 to 639, rows 0 to 39. Source: systems/hud.md, Presentation; scope report DRA-23, Player sees.
- **Blink (`/`, no key held):** read the canvas pixel at the ship's center, (320, 240), on every frame from the fall until about 1 s after it. In the first 0.5 s after the respawn it is white (the ship) for about 0.1 s, then not white for about 0.1 s, and so on: three white spans and two not-white spans. After that it stays white. In `?debug=1`, `invulnerable end` follows the `respawn from` line by about 0.5 s. Source: systems/run.md, Diagram (blink timeline) and Rules; scope report DRA-23, Limits.
- **The wait (`?debug=1`, no key held):** after the respawn, wait 5 s. The overlay reads `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00` the whole time. The only new line is `invulnerable end`. The meters readout keeps counting, about 33 m more in the 5 s, and the stars keep moving. Source: 05-lives-and-damage.md, rule 2.5; systems/run.md, Rules, steps 3 and 4.
- **A press ends the wait and thrusts (`?debug=1`):** while the ship waits, tap ArrowUp for about 0.2 s. The log shows `key down key=up x=320.00 y=240.00`, then `respawn wait end`, then `key up key=up x=320.00 y=...` with y below 240.00: the ship rose from the first tick. After the release the ship falls under gravity. Source: 05-lives-and-damage.md, rule 2.5; 91-decision-log.md, row 28.
- **A held key doesn't end the wait (`?debug=1`):** hold ArrowDown from the start, so the ship dives off the floor and respawns with Down still held. Keep holding for 2 s: no `respawn wait end`, and the overlay stays at `x 320.00 y 240.00 vx 0.00 vy 0.00`. Release Down, then tap ArrowLeft: `respawn wait end`, and the ship moves left. Source: systems/run.md, Rules, step 1 and Rationale.
- **Game over (`?debug=1`):** let the ship fall three times, ending each wait with a short tap of ArrowUp. After the third fall: `life lost lives=0`, then INFO `game over meters=<n>`, and no `respawn from` line after it. The canvas shows no heart, and the Game Over box: inside x 160 to 479, rows 180 to 299, star pixels are darker than outside (about (58, 65, 91) instead of (90, 100, 140)), and the white text "Game Over" with "Press any arrow to retry" below it, both centered, matches reference text rendered with the game's default font at 32 px and 16 px. No white ship pixel anywhere: the ship stays below the floor. Source: systems/run.md, Rules, step 5.3 and Presentation; 02-game-flow.md, rule 5; scope report DRA-23, Values needed (Game Over box).
- **Everything freezes (`?debug=1`):** on the Game Over box, two canvas reads 2 s apart are identical: stars, readout, overlay values (the overlay shows the y the ship fell from, at least 496.00). No `scroll start`, `wall hit`, `top line stop` or `respawn` line appears. Source: 02-game-flow.md, rule 5.
- **Retry needs a fresh press (`?debug=1`):** make the third fall a dive with ArrowDown held, and keep holding it for 2 s after the box appears: no `new run`. Press F3 twice: only `overlay visible=...` lines, no `new run`. Release Down, wait about 0.5 s, then tap ArrowLeft: INFO `new run`. Source: 02-game-flow.md, rule 6 and Edge cases; retry_key (locked); 91-decision-log.md, row 31.
- **A new run plays like the first (`?debug=1`, right after the retry):** the box is gone, the readout reads `0 m`, three hearts show, and the ship falls from the center with no wait and no blink. `scroll start tick=31` appears about 0.5 s after `new run`. The next fall, about 1.07 s after `new run`, logs `life lost lives=2`. Source: 02-game-flow.md, rules 3 and 6; 91-decision-log.md, row 30.
- **Normal mode (`/`):** the same game over and retry by pixels only: after three falls the box shows; a fresh arrow press clears it and shows three hearts and `0 m`. No (0, 255, 0) pixels at any point.
- **Package contents:** as for DRA-13, and `core/run.py` and `ui/game_over.py` must be in `game.apk`.

Integration checks for DRA-29, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background, debug mode: the test spawn list places meteorite id 1 (small, x 160) on tick 1, id 2 (medium, x 320) on tick 61, id 3 (big, x 480) on tick 121, then ids 4, 5, 6 on ticks 181, 241, 301, and so on. Each shows its warning for 60 ticks (1.0 s), then falls at 2.4675 px a tick (about 148 px a second). A medium meteorite at x 320 reaches a ship hovering on the top line about 69 ticks after it appears (3.17 s after play start for id 2), and a ship standing at the respawn point about 91 ticks after (3.53 s for id 2). Timings updated by the 2026-10-15 hotfix (91-decision-log.md, row 40).

Earlier checks in debug mode, reworded for DRA-29. Normal-mode checks (`/`) don't change: nothing spawns there.
- Lines starting with `drifter ` are expected in every debug-mode check and are left out of every count and "only new line" in the DRA-6 to DRA-23 checks.
- **DRA-6, Log by event:** the waiting part becomes: with the ship waiting at the respawn point and no key held, from the respawn until 4 s after it, the new lines are one `invulnerable end` from the fall; then, from medium meteorite id 2 reaching the ship about 3.53 s after play start, one `drifter touch id=2 type=meteorite effect=hit`, one `life lost lives=1` and, 0.5 s later, one `invulnerable end`. Never a line per tick.
- **DRA-13, No overlap in debug mode:** "The overlay shows only x, y, vx and vy and its two lines" now reads: in the top-left text area, the overlay shows only those four lines, as in DRA-6. Hitbox outlines and drifter labels elsewhere are expected.
- **DRA-23, The wait:** wait 4 s after the respawn, not 5 s, so the run ends before the second medium meteorite (id 5) reaches the ship at about 6.53 s. The overlay reads `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00` the whole time: a hit doesn't move the ship. The new lines are those in the DRA-6 rewording above. The meters readout gains about 26 m in the 4 s.
- **DRA-23, Game over and Retry needs a fresh press:** a medium meteorite at x 320 can now cost one of the three lives before the third fall. Both checks are about a game over by a fall, so they pass when it is one: `life lost lives=0` follows the fall with no `drifter touch` just before it, and no white ship pixel shows. Ending each wait with a prompt tap usually finishes the three falls before medium id 5 arrives (about 6.5 s). If a hit takes a life first, repeat the check in a fresh page. A game over by a hit is checked in the DRA-29 checks below.

New checks:
- **Tuning loaded (`/` and `?debug=1`):** one INFO line `tuning loaded drifters=meteorite hazard_speed_scaling=True timer_scaling=True`, after the start line and before the first `scroll start`. Source: this contract, Rules, Tuning loader.
- **The ship is an inverted T (`/`):** on one of the first frames (within 0.1 s of play start, the ship near y 240): (320, 230) is white (the bar); (308, 230) and (331, 230) are not white; (308, 250) and (331, 250) are white (the foot). Source: systems/ship.md, Presentation; 04-ship.md, placeholder_look.
- **Normal mode spawns nothing (`/`):** for 5 s, no (255, 220, 120) and no (140, 140, 140) pixel anywhere on the canvas. Source: scope report DRA-29, Feature.
- **The test spawn list (`?debug=1`, no key held):** in the first 5 s the log shows, in this order of time: `drifter spawn id=1 type=meteorite variant=small x=160.00 y=-10.00 speed=2.4x level=1` right after play start (2.4675 rounded to two decimals); about 1 s later `drifter active id=1 type=meteorite x=160.00 y=-10.00`; about 1 s after id 1, `drifter spawn id=2 ... variant=medium x=320.00 y=-14.00`; about 2 s after id 1, `drifter spawn id=3 ... variant=big x=480.00 y=-20.00`; about 4.4 s after play start, `drifter gone id=1 type=meteorite x=160.00 y=...` with y at least 490.00; about 3 s after id 1, `drifter spawn id=4 ... variant=small`. Each id has exactly one `drifter spawn`, one `drifter active` and, once it has left, one `drifter gone`. Source: scope report DRA-29, Test spawn list; systems/run.md, Logging; drifters.md, Diagram (timeline).
- **Warning, then the rock (`?debug=1`):** within the first 1 s, the canvas has glow pixels (255, 220, 120) within 12 px of (160, 12) and none farther from it than 12 px in x or y (the 24 px warning, the same for every drifter), and grey pixels (140, 140, 140) within 7 px of (160, 12): the 14 px copy just inside the top edge. At about 1.2 s, no glow pixel remains near (160, 12), and grey pixels lie in columns 150 to 169 below row 0. Two reads 0.5 s apart show the grey disc about 74 px lower. Source: 07-drifters.md, rule 9 and entry_warning values; drifters/01-meteorite.md, rules 1 and 3.
- **A hit costs one life, once (`?debug=1`):** hold ArrowUp from play start for about 10 s, so the ship sits on the top line at x 320. About 3.2 s after play start: `drifter touch id=2 type=meteorite effect=hit`, then `life lost lives=2`, and no `respawn from`. The pixel at the ship's center (320, 184) blinks for 0.5 s, then stays white. id 2 never logs a second `drifter touch` (the meteorite-only stand-in, scope report DRA-29, Stand-ins). About 6.2 s: `drifter touch id=5 ...` and `life lost lives=1`. About 9.2 s: `drifter touch id=8 ...`, `life lost lives=0`, INFO `game over meters=<n>`. No `drifter touch` line for any small or big meteorite (ids 1, 3, 4, 6, 7). When ArrowUp is released, its `key up` line shows `x=320.00 y=184.00`: the hits never moved the ship. Source: 05-lives-and-damage.md, rules 1 and 5; systems/run.md, Rules, step 7.
- **Game over freezes the drifters, retry clears them (`?debug=1`):** right after the game over above, two canvas reads 2 s apart are identical, and no `drifter` line appears. Release ArrowUp, then tap ArrowLeft: INFO `new run`, then `drifter spawn id=1 ... variant=small` within about 0.1 s. The first frame after `new run` has no grey pixel outside the new warning near (160, 10). Source: 02-game-flow.md, rules 5 and 6; systems/run.md.
- **Outlines and labels (`?debug=1`):** about 2.5 s after play start, with medium id 2 active: green (0, 255, 0) pixels on two circles around the rock's center, radius about 14 and about 28 (its hitbox and graze zone), and green pixels on the outline of the ship's T. Below the rock, green text that matches `meteorite medium x 320.00 y <y> active` rendered with the game's default font at 16 px. While a warning shows, its label sits against the top edge. Press F3: every green pixel goes (outlines, labels, text, lines). F3 again brings them back. Source: 10-ui.md, debug_overlay; systems/debug-overlay.md, Presentation.
- **Bad tuning file (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change. Copy `game/tuning/` to a scratch folder and set `"speed_ratio": "fast"` in its `drifters/meteorite.json`. From the command line, import `app.tuning`, set `app.tuning.TUNING_DIR` to the scratch folder, then call `run()`. The log shows the start line, then ERROR `unexpected error, showing the error screen` with a `ValueError` whose message names `tuning/drifters/meteorite.json` and `speed_ratio`. No `error screen failed` line. The error screen is drawn and the process idles until it is stopped. Source: this contract, Rules, Tuning loader; 15-tech-constraints.md, rule 8.
- **Package contents:** as for DRA-23, and `core/collision.py`, `core/levels.py`, every file in `core/drifters/`, `ui/shapes.py`, every file in `ui/drifters/`, `app/tuning.py`, `app/debug_spawns.py`, `tuning/drifters/meteorite.json` and `tuning/playtest.json` must be in `game.apk`.

Integration checks for DRA-39, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: the committed `game/tuning/debug_spawns.json` holds the three DRA-29 meteorite rows (small x 160, medium x 320, big x 480, in that order) and some satellite rows, with `"mode": "meteorite"`, so in debug mode the three rocks fall on their DRA-29 ticks (1, 61, 121, then every 180 ticks) and every DRA-29 debug check keeps its numbers. Checks marked **(satellite mode)** need `"mode": "satellite"` in that file: the Director switches it, or allows the Integration Engineer to switch it for the run and put it back after. Positions are on the 640 × 480 canvas. Satellite numbers at Level 1: flat 2.4675 px a tick across (148 px a second); angled about 2.3187 across and 0.8439 down.

Earlier checks, reworded for DRA-39:
- **DRA-29, Tuning loaded:** the line now reads `tuning loaded drifters=meteorite,satellite hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75` with the committed `hazards.json` (whether it sets both values or leaves them out). Still after the start line and before the first `scroll start`.
- **DRA-29, A hit costs one life, once:** id 2 still never logs a second `drifter touch`, now because it leaves the screen (about 2.3 s after the touch) before its 3 s re-hit cooldown ends, not because of the DRA-29 stand-in.
- **DRA-29, Normal mode spawns nothing:** also no (240, 240, 240) and no (60, 110, 220) pixel anywhere for 5 s.
- Every other DRA-29 check stands as written.

New checks:
- **Spawn list loaded (`?debug=1`):** one INFO line `debug spawns loaded mode=meteorite rows=3 loop_ticks=180` (or the committed `loop_ticks` if the file sets it), after `tuning loaded` and before the first `scroll start`. In `/` there is no such line. Source: this contract, Rules, Debug test spawn list.
- **Dim after a hit (`?debug=1`, hold ArrowUp from play start):** about 1 s after `drifter touch id=2 type=meteorite effect=hit` (so about 4.2 s after play start), in columns 306 to 334 between rows 250 and 479 there are (105, 105, 105) pixels (the medium rock at 0.75 brightness) and no (140, 140, 140) pixel. At the same moment the small rocks near x 160 show (140, 140, 140) and no (105, 105, 105): only the hazard that hit is dim. Source: 05-lives-and-damage.md, rule 1.5, rehit_dim (guess); systems/drifters.md, Presentation, Brightness.
- **Satellite warning (satellite mode, `?debug=1`):** for the first row in play, if it is flat, has no `invert` and no `x`, with y `Y`: within its first 1 s, glow pixels (255, 220, 120) lie within 12 px of (12, Y) and none farther from it than 12 px in x or y; white (240, 240, 240) pixels lie within 3 px of (12, Y) (the 4.7 × 4.7 body) and blue (60, 110, 220) pixels in columns 5 to 19, within 2 rows of Y (the 14 × 2.3 bar). The log shows `drifter spawn id=1 type=satellite variant=flat x=-18.00 y=<Y> speed=2.47 level=1`, then about 1 s later `drifter active id=1 type=satellite x=-18.00 y=<Y>`. Source: drifters/02-satellite.md, rules 1 and 7, start, placeholder_look; systems/drifters.md, Presentation, Entry warning.
- **Satellite crosses and leaves (satellite mode, `?debug=1`):** after that `drifter active` line, white body pixels appear at the left edge in rows Y − 6 to Y + 5 (it was not removed while it sat outside the wall). Two canvas reads 0.5 s apart while it crosses show the white body about 74 px further right in the same rows, and the blue bar 36 px wide behind it. About 4.6 s after `drifter active` (274 ticks), `drifter gone id=1 type=satellite x=<x> y=<Y>` with x at least 658.00. Source: drifters/02-satellite.md, rules 3 and 5; 07-drifters.md, rule 12; 91-decision-log.md, row 58.
- **Angled and inverted (satellite mode, `?debug=1`):** for a row in play with `"variant": "angled"` and `"invert": true` and no `x`, with y `Y`: its warning glow sits within 12 px of (628, Y); the blue pixels of its copy run down to the left (the leftmost blue column's lowest blue pixel is lower than the rightmost column's). Once active, two reads 0.5 s apart show the white body about 70 px further left and about 25 px lower, and its boxes stay upright (the body's white pixels form a square). Source: drifters/02-satellite.md, rules 1, 3 and 8; variants (guess).
- **Shared hazard values (desktop, headless, `SDL_VIDEODRIVER=dummy`):** no code change. Copy `game/tuning/` to a scratch folder and write `{"rehit_cooldown": 5}` to its `hazards.json`. Import `app.tuning`, set `app.tuning.TUNING_DIR` to the scratch folder, then call `run()`. The log's `tuning loaded` line ends `rehit_cooldown=5 rehit_dim=0.75`: the field left out keeps its default. Source: scope report DRA-39, Limits.
- **Bad spawn list (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change. In a scratch copy of `game/tuning/`, add the row `{"type": "satellite", "x": 100}` to `debug_spawns.json`. Point `app.tuning.TUNING_DIR` at it and call `run()`. The log shows ERROR `unexpected error, showing the error screen` with a `ValueError` whose message names `tuning/debug_spawns.json`, the row as `rows[<i>]` and `satellite placement needs y`. No `error screen failed` line. The error screen is drawn and the process idles until it is stopped. Repeat with the rows as committed and `"mode": "ufo"`: the message names `mode`. Source: this contract, Rules, Debug test spawn list; 15-tech-constraints.md, rule 8.
- **Normal mode ignores the list (desktop, headless, `SDL_VIDEODRIVER=dummy`, no `DRIFTWARD_DEBUG`):** with the broken scratch list from the check above, `run()` logs `start mode=normal` and `tuning loaded ...`, no `debug spawns loaded`, no ERROR, and runs frames until stopped. Source: 15-tech-constraints.md, rule 7.
- **Package contents:** as for DRA-29, and `core/drifters/satellite.py`, `ui/drifters/satellite_view.py`, `tuning/drifters/satellite.json`, `tuning/hazards.json` and `tuning/debug_spawns.json` must be in `game.apk`.

Integration checks for DRA-47, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: the committed `game/tuning/debug_spawns.json` keeps its meteorite and satellite rows and its `loop_ticks` 180, and gains these eight chain lightning rows, in this order (scope report DRA-47, Limits: example rows for every variant):
1. `{"type": "chain_lightning", "x": 320, "speed": 2.0}` (pair_flat, the default)
2. `{"type": "chain_lightning", "x": 120, "variant": "pair_diagonal"}`
3. `{"type": "chain_lightning", "x": 580, "variant": "pair_vertical"}`
4. `{"type": "chain_lightning", "x": 160, "variant": "trio_line"}`
5. `{"type": "chain_lightning", "x": 520, "variant": "trio_diagonal", "invert": true}`
6. `{"type": "chain_lightning", "x": 120, "variant": "trio_l", "invert": true}`
7. `{"type": "chain_lightning", "x": 520, "variant": "trio_triangle"}`
8. `{"type": "chain_lightning", "x": 520, "variant": "trio_triangle", "invert": true}`

Only row 1 crosses the ship's column (x 304 to 336); its `speed` 2.0 brings its arc to the ship's respawn point on its first fire state. Checks marked **(chain lightning mode)** need `"mode": "chain_lightning"` in that file: the Director switches it, or allows the Integration Engineer to switch it for the run and put it back after. In that mode the eight rows are placed on ticks 1, 23, 46, 68, 91, 113, 136 and 158, then every 180 ticks (ids 1 to 8, then 9 to 16, ...). Positions are on the 640 × 480 canvas. With no key held, the ship falls on tick 64 and then waits at (320, 240).

Earlier checks, reworded for DRA-47:
- **DRA-39, Tuning loaded** (and DRA-29's): the line now reads `tuning loaded drifters=meteorite,satellite,chain_lightning hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45` with the committed `hazards.json` (whether it sets the values or leaves them out). Still after the start line and before the first `scroll start`.
- **DRA-29, Normal mode spawns nothing:** also no (0, 220, 255), no (120, 200, 255) and no (220, 240, 255) pixel anywhere for 5 s.
- **DRA-39, Spawn list loaded:** `rows=` counts the rows in play in the committed mode; in chain lightning mode it reads `debug spawns loaded mode=chain_lightning rows=8 loop_ticks=180`.
- Every other check stands as written. A mode other than `chain_lightning` leaves the chain lightning rows out of play, so the meteorite and satellite checks keep their numbers.

New checks:
- **Chain lightning warning (chain lightning mode, `?debug=1`):** the log shows `drifter spawn id=1 type=chain_lightning variant=pair_flat x=320.00 y=-6.00 speed=2.00 level=1` right after play start. Within the first 0.3 s (before id 2 is placed), glow pixels (255, 220, 120) lie within 12 px of (256, 12) and none lies farther than 12 px from it in x or y: the warning sits above the left node (the tie between two nodes equally near the ship goes to the left one) and is the same 24 px size as every warning. Cyan (0, 220, 255) pixels lie within 2 px of (250, 18), (256, 6) and (262, 18): the triangle copy, scaled to 14 px wide, though id 1 is a pair. No cyan pixel lies within 10 px of (384, 12). Source: drifters/03-chain-lightning.md, rule 2, entry_warning_icon, entry_warning_size; systems/drifters.md, Rules, Chain lightning (Warning node, Warning place, Warning copy).
- **The charge (chain lightning mode, `?debug=1`):** about 1 s after play start, `drifter active id=1 type=chain_lightning x=320.00 y=-6.00`. Around id 1's two nodes (x 256 and 384, falling 2 px a tick), ray pixels (120, 200, 255) within 13 px of each node's center: about 1.25 s after play start, only up and to the right of each node; about 1.75 s, only above each node's row (up right and up left); about 2.75 s, in all four diagonal directions. Between those reads the cyan discs are about 60 px lower each 0.5 s. No (220, 240, 255) pixel in columns 262 to 378 before about 3.0 s. Source: drifters/03-chain-lightning.md, telegraph, charge_rays, ray_length, placeholder_look; 91-decision-log.md, row 62.
- **Nothing hits while it charges, the fire does (chain lightning mode, `?debug=1`, no key held):** after the fall (`life lost lives=2`, `respawn from x=320.00 ...`), the ship waits at (320, 240). From about 2.9 s after play start id 1's line between its nodes crosses the ship's bar while it still charges: no `drifter touch`. About 3.0 s after play start (tick 181, its first fire state): `drifter touch id=1 type=chain_lightning effect=hit`, then `life lost lives=1`, and no `respawn from` after it. No `drifter touch` for any id other than 1 or 9 in this check. About 6.0 s (tick 361), id 9, row 1 again, does the same: `drifter touch id=9 ...`, `life lost lives=0`, INFO `game over meters=<n>`. Source: drifters/03-chain-lightning.md, rules 3, 5 and 6; 05-lives-and-damage.md, rule 1.
- **The arcs (chain lightning mode, `?debug=1`):** about 4.2 s after play start (id 4, `trio_line` at x 160, about 4 ticks into its first fire), band pixels (220, 240, 255) in rows 296 to 304 at columns 40 to 150 and 170 to 280 (both arcs), with cyan discs centered near x 32, 160 and 288 on those rows. Source: drifters/03-chain-lightning.md, rules 5 and 9, placeholder_look; Layouts.
- **The whole chain dims after a hit (chain lightning mode, `?debug=1`, no key held):** about 3.5 s after play start (0.5 s after id 1's touch), id 1's nodes near (256, 294) and (384, 294) show (0, 165, 191) and no (0, 220, 255) within 6 px of those centers; in columns 300 to 340 near row 294 the band shows (165, 180, 191) and no (220, 240, 255). Source: 05-lives-and-damage.md, rule 1.5, rehit_dim (guess); systems/drifters.md, Presentation, Brightness.
- **Outlines (chain lightning mode, `?debug=1`):** during id 4's fire, green (0, 255, 0) outline pixels run along both edges of each arc (rows about 297 and 303) and around each node, and a wider green outline about 14 px out (the graze zone). While a chain charges, it has no outline, only its label. Source: systems/debug-overlay.md, Presentation; systems/drifters.md, Presentation, Line shape.
- **Every variant (chain lightning mode, `?debug=1`, hold ArrowUp from play start for about 10 s):** the ship sits on the top line at x 320, above where id 1 and id 9 fire, so no `drifter touch` line appears and no game over comes. Over those 10 s each of ids 1 to 8 logs `drifter spawn` with its row's variant and x, `drifter active`, and, once it has left, `drifter gone` with y at least 486 (id 8 last, about 7.7 s after play start). A screenshot at about 5.8 s, while ids 7 and 8 fire, shows id 7's triangle point up and id 8's (inverted) point down; id 6 (`trio_l`, inverted) shows its corner at the bottom right. Source: drifters/03-chain-lightning.md, Layouts; rule 7.
- **Bad chain lightning file (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change. In a scratch copy of `game/tuning/`, set the `arcs` of `trio_l` in `drifters/chain_lightning.json` to `[[0, 2]]`. Point `app.tuning.TUNING_DIR` at it and call `run()`. The log shows ERROR `unexpected error, showing the error screen` with a `ValueError` naming `tuning/drifters/chain_lightning.json` and `variants.trio_l.arcs[0]`. Repeat with `"telegraph_min": true` in `hazards.json`: the message names `tuning/hazards.json` and `telegraph_min`. No `error screen failed` line. Source: this contract, Rules, Tuning loader; 15-tech-constraints.md, rule 8.
- **Package contents:** as for DRA-39, and `core/drifters/chain_lightning.py`, `ui/drifters/chain_lightning_view.py` and `tuning/drifters/chain_lightning.json` must be in `game.apk`.

Integration checks for DRA-56, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: the committed `game/tuning/debug_spawns.json` keeps its other rows and its `loop_ticks` 180, and gains these six fireball rows, in this order (scope report DRA-56, Limits: example rows for both variants, both directions and all three entries):
1. `{"type": "fireball", "x": 125}` (small, along the top, flies down and to the right)
2. `{"type": "fireball"}` (small, the top-left corner)
3. `{"type": "fireball", "variant": "big", "invert": true}` (big, the top-right corner, flies down and to the left)
4. `{"type": "fireball", "y": 120}` (small, the left wall)
5. `{"type": "fireball", "y": 200, "variant": "big", "invert": true}` (big, the right wall)
6. `{"type": "fireball", "x": 560, "invert": true, "speed": 2.0}` (small, along the top, flies down and to the left, slower)

Only row 1 meets a ship waiting at the respawn point (320, 240); none meets a ship held on the top line at (320, 184). Checks marked **(fireball mode)** need `"mode": "fireball"` in that file: the Director switches it, or allows the Integration Engineer to switch it for the run and put it back after. In that mode the six rows are placed on ticks 1, 31, 61, 91, 121 and 151, then every 180 ticks (ids 1 to 6, then 7 to 12, ...). Each shows its warning for 60 ticks, so ids 1 to 6 appear on ticks 61, 91, 121, 151, 181 and 211. Level 1 speed 3.0926 px a tick along the path: about 1.77 across and 2.53 down per tick (106 px across and 152 px down a second); row 6 at 2.0: about 1.15 and 1.64. Positions are on the 640 × 480 canvas. With no key held, the ship falls on tick 64 and then waits at (320, 240).

Earlier checks, reworded for DRA-56:
- **DRA-47, Tuning loaded** (and DRA-39's and DRA-29's): the line now reads `tuning loaded drifters=meteorite,satellite,chain_lightning,fireball hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45` with the committed `hazards.json`. Still after the start line and before the first `scroll start`.
- **DRA-29, Normal mode spawns nothing:** also no (255, 140, 0) and no (200, 160, 0) pixel anywhere for 5 s.
- **DRA-39, Spawn list loaded:** in fireball mode it reads `debug spawns loaded mode=fireball rows=6 loop_ticks=180`.
- Every other check stands as written. A mode other than `fireball` leaves the fireball rows out of play, so the earlier checks keep their numbers.

New checks:
- **Fireball warning, tilted (fireball mode, `?debug=1`):** the log shows `drifter spawn id=1 type=fireball variant=small x=125.00 y=-10.50 speed=3.09 level=1` right after play start. Within the first 0.5 s (before id 2 is placed), glow pixels (255, 220, 120) lie within 12 px of (125, 12) and none lies farther than 12 px from it in x or y. Orange (255, 140, 0) and dark yellow (200, 160, 0) pixels lie within 8 px of (125, 12), and the mean position of the orange pixels is to the right of and below the mean of the dark yellow ones: the copy points down and to the right, the tail back. Source: drifters/06-fireball.md, rule 1, placeholder_look; 07-drifters.md, rule 9 and entry_warning_size; systems/drifters.md, Rules, Fireball (Warning place, Warning tilt, Warning copy).
- **Every entry's warning (fireball mode, `?debug=1`):** at about 1.2 s the warnings of id 2 and id 3 show at once: glow within 12 px of (12, 12) and of (628, 12). In id 3's copy (`invert`), the mean of the orange pixels is to the left of and below the mean of the dark yellow ones. At about 1.7 s, id 4's warning: glow within 12 px of (12, 120). At about 2.2 s, id 5's: glow within 12 px of (628, 200), its orange mean left of and below its yellow mean. The log shows `drifter spawn id=2 type=fireball variant=small x=0.00 y=-10.50 speed=3.09 level=1`, `id=3 ... variant=big x=640.00 y=-16.00`, `id=4 ... variant=small x=-10.50 y=120.00`, `id=5 ... variant=big x=656.00 y=200.00` and `id=6 ... variant=small x=560.00 y=-10.50 speed=2.00`. Source: drifters/06-fireball.md, rules 1 and 3, start; 07-drifters.md, rule 9.
- **It flies (fireball mode, `?debug=1`):** about 1 s after play start, `drifter active id=1 type=fireball x=125.00 y=-10.50`. Two canvas reads 0.5 s apart while id 1 flies (about 1.5 s and 2.0 s after play start) show its orange disc (21 px across) about 53 px further right and 76 px lower, with a dark yellow disc (about 11 px across) touching it up and to the left. Source: drifters/06-fireball.md, rules 3 and 7, placeholder_look, speed.
- **A touch costs a life (fireball mode, `?debug=1`, no key held):** after the fall (`life lost lives=2`, `respawn from x=320.00 ...`), the ship waits at (320, 240). About 2.65 s after play start (tick 159): `drifter touch id=1 type=fireball effect=hit`, then `life lost lives=1`, and no `respawn from` after it. About 5.65 s (tick 339), id 7 (row 1 again) does the same: `drifter touch id=7 ...`, `life lost lives=0`, INFO `game over meters=<n>`. No `drifter touch` for any other id. Source: drifters/06-fireball.md, rule 4; 05-lives-and-damage.md, rule 1.
- **It dims after the hit (fireball mode, `?debug=1`, no key held):** about 3.15 s after play start (0.5 s after id 1's touch), id 1's head near (352, 314) shows (191, 105, 0) and no (255, 140, 0) within 9 px of that point, and its tail near (343, 301) shows (150, 120, 0) and no (200, 160, 0). Source: 05-lives-and-damage.md, rule 1.5, rehit_dim (guess); systems/drifters.md, Presentation, Brightness.
- **Nothing visible when it goes (fireball mode, `?debug=1`, no key held):** read the canvas on every frame from about 4.25 s to 4.45 s after play start, in rows 465 to 479 and columns 440 to 500. There are frames with dark yellow (200, 160, 0) or (150, 120, 0) pixels (id 1's tail, still dim) and no orange or dimmed orange pixel there: the head has left, the tail still shows. `drifter gone id=1 type=fireball x=483.32 y=501.23` comes only after the last frame with those tail pixels. Source: drifters/06-fireball.md, rule 5; 07-drifters.md, rule 12; 91-decision-log.md, row 64.
- **Every row leaves (fireball mode, `?debug=1`, hold ArrowUp from play start for about 9 s):** the ship sits on the top line at x 320; no `drifter touch` line appears and no game over comes. Each of ids 1 to 6 logs one `drifter spawn`, one `drifter active` and one `drifter gone`: id 1 `x=483.32 y=501.23` (about 4.4 s), id 2 `x=358.32 y=501.23` (about 4.9 s), id 3 `x=271.04 y=510.93` (about 5.5 s), id 4 `x=255.58 y=500.00` (about 5.0 s), id 5 `x=437.82 y=511.60` (about 5.1 s), id 6 `x=202.09 y=500.65` (about 8.7 s). Each leaves at the bottom; ids 3, 5 and 6 left of where they started. Source: drifters/06-fireball.md, rules 3 and 5; systems/drifters.md, Diagram (fireball timeline).
- **Outlines (fireball mode, `?debug=1`):** while id 1 flies, green (0, 255, 0) outline pixels lie on a circle of radius about 10 around its head and about 5 around its tail, and on wider circles about 14 px further out (the graze zones). Its label sits under the head. Source: systems/debug-overlay.md, Presentation.
- **Bad fireball file and a row with no position (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change. In a scratch copy of `game/tuning/`, set `"tail_ratio": 0` in `drifters/fireball.json`. Point `app.tuning.TUNING_DIR` at it and call `run()`. The log shows ERROR `unexpected error, showing the error screen` with a `ValueError` naming `tuning/drifters/fireball.json` and `tail_ratio`. Repeat with the file as committed and the row `{"type": "satellite"}` added to `debug_spawns.json`: the message names `tuning/debug_spawns.json`, the row as `rows[<i>]` and `satellite placement needs y`. No `error screen failed` line. Source: this contract, Rules, Tuning loader and Debug test spawn list; 15-tech-constraints.md, rule 8.
- **Package contents:** as for DRA-47, and `core/drifters/fireball.py`, `ui/drifters/fireball_view.py` and `tuning/drifters/fireball.json` must be in `game.apk`.

Integration checks for DRA-61, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: the score equals the meters flown, 1 point a meter (`systems/run.md`, Rules, Score). The world scrolls 1.1 px a tick from tick 31, so the score reaches 1 on tick 40 (about 0.67 s), about 62 at 10 s, and 1 000 on tick 9121 (about 152 s). "Reference text" means the text rendered in the same page with the game's default font at the stated size, in white (255, 255, 255). `score_text` is the format in `systems/hud.md`, Presentation: `SCORE`, a space, the digits in groups of three split by one space.

Earlier checks, reworded for DRA-61. Wherever an earlier check reads "the readout", "the meters readout" or `<n> m`, it now reads the SCORE line at HUD line 1, with the same number:
- **DRA-6, Catch-up cap:** SCORE doesn't jump by the hidden time's distance.
- **DRA-13, Readout counts up**, now **SCORE counts up (`/`):** a screenshot right after play starts shows `SCORE 0` at the top left, its text top near y 4, matching reference text at 16 px. Screenshots about 5 s and 10 s later, with no key held, show larger whole numbers, the 10 s one about 62. Within a run the number never goes down.
- **DRA-13, Hovering still earns meters:** SCORE keeps counting at the same rate as with no key held.
- **DRA-13, No overlap in debug mode:** the white SCORE line sits below the overlay's fourth line, with a gap and no shared pixel row, and stays exactly where it was while F3 hides the overlay.
- **DRA-23, The wait** (and its DRA-29 rewording): SCORE keeps counting, about 33 more in the 5 s (about 26 in the 4 s).
- **DRA-23, Game over:** the Game Over box now holds three white lines, all centered: "Game Over", then `score_text(<n>)` with `<n>` from the `game over meters=<n>` line (for example `SCORE 23`), then "Press any arrow to retry". They match reference text at 32, 16 and 16 px.
- **DRA-23, Everything freezes:** the two canvas reads 2 s apart are identical, SCORE and the box's score line included.
- **DRA-23, A new run plays like the first** and **Normal mode:** SCORE reads `SCORE 0` where they read `0 m`.
- Every other check stands as written.

New checks:
- **No meters readout (`/`, no key held):** for 10 s after play starts, no white (255, 255, 255) pixel lies in x 0 to 299, rows 20 to 47 (HUD line 2), while SCORE counts on line 1 above it. In `?debug=1`, the same holds for the 28 rows starting one HUD line spacing (20 px) below the SCORE line's top, left of x 300. Source: scope report DRA-61, Limits; systems/hud.md, Presentation.
- **Digits in groups (`/`, hold ArrowUp from play start):** the ship sits on the top line and normal mode spawns nothing, so the run lasts. Between about 153 s and 160 s after play start, SCORE matches reference text of one of `SCORE 1 000` to `SCORE 1 052` at 16 px: a 1, one space, then three digits. Source: scope report DRA-61, Limits (format); systems/hud.md, Presentation.
- **The final score (`?debug=1`):** end a run as in the DRA-23 game over check. The box's score line and the HUD's SCORE line show the same text, `score_text(<n>)` with `<n>` from `game over meters=<n>`, and it doesn't change while the box shows. Release every arrow and tap one: INFO `new run`, the box is gone and SCORE reads `SCORE 0`. Source: 02-game-flow.md, rules 3, 5 and 6; systems/run.md, Rules, Score.
- **Package contents:** as for DRA-56, and `ui/score_text.py` must be in `game.apk`.

Integration checks for DRA-62, on top of the required browser checks and every earlier check above, as reworded below (all must still pass). Each check starts in a fresh page unless it says otherwise. Background: the committed `game/tuning/debug_spawns.json` keeps its other rows and its `loop_ticks` 180, and gains these four coin rows, in this order (scope report DRA-62, Limits: example rows for both variants):
1. `{"type": "coin", "x": 320}` (common, from the top, in the ship's column)
2. `{"type": "coin", "x": 200, "variant": "rare"}` (rare, from the top)
3. `{"type": "coin", "x": 440, "y": 210}` (common, placed on screen)
4. `{"type": "coin", "x": 320, "y": 230, "variant": "rare"}` (rare, placed on screen, over the respawn point)

Checks marked **(coin mode)** need `"mode": "coin"` in that file: the Director switches it, or allows the Integration Engineer to switch it for the run and put it back after. In that mode the four rows are placed on ticks 1, 46, 91 and 136, then every 180 ticks (ids 1 to 4, then 5 to 8, ...). A coin has no warning: it is on the field from the tick it is placed. It moves only with the world: still until tick 31, then 1.1 px a tick down (33 px in 0.5 s), never sideways. With ArrowUp held from play start the ship sits on the top line at (320, 184); with no key held it falls on tick 64 and then waits at (320, 240). The coin's colors: lit (200, 30, 90), shade (70, 0, 60), rim and ring (255, 80, 150), rare glint (255, 220, 240); the popup is (255, 80, 150) too. Positions are on the 640 × 480 canvas.

Earlier checks, reworded for DRA-62:
- **DRA-56, Tuning loaded** (and every earlier one): the line now reads `tuning loaded drifters=meteorite,satellite,chain_lightning,fireball,coin hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45` with the committed `hazards.json`.
- **DRA-29, Normal mode spawns nothing:** also no (200, 30, 90), no (70, 0, 60) and no (255, 80, 150) pixel anywhere for 5 s.
- **DRA-39, Spawn list loaded:** in coin mode it reads `debug spawns loaded mode=coin rows=4 loop_ticks=180`.
- Every other check stands as written. A mode other than `coin` leaves the coin rows out of play, so the earlier checks keep their numbers.

New checks:
- **No warning (coin mode, `?debug=1`, hold ArrowUp):** right after play start the log shows `drifter spawn id=1 type=coin variant=common x=320.00 y=-10.00 speed=0.00 level=1`, and later `id=2 ... variant=rare x=200.00 y=-10.00`, `id=3 ... variant=common x=440.00 y=210.00` and `id=4 ... variant=rare x=320.00 y=230.00`, each with `speed=0.00`. No `drifter active` line for any coin, ever. For 10 s no glow pixel (255, 220, 120) shows anywhere. During the first 0.5 s no coin color shows anywhere; from about 0.52 s (tick 31) id 1's tip shows on row 0 at x 319 and 320, and it scrolls down from there. id 3 shows at about (440, 210) on the first frame after its `drifter spawn` line (about 1.52 s), with nothing drawn there before. Source: drifters/04-coin.md, entry_warning (locked), rules 1 and 3; 07-drifters.md, rule 9; scope report DRA-62, Limits; systems/drifters.md, Rules, Coin.
- **Its look (coin mode, `?debug=1`, hold ArrowUp):** at about 1.6 s, id 3's crystal: lit (200, 30, 90) pixels only left of its middle column and shade (70, 0, 60) only from it rightward, 12 columns and 20 rows in all, a pink (255, 80, 150) outline around it, and a pink 1 px ring reaching 11 px left and 10 px right of the crystal's middle on 8 rows across it. No (255, 220, 240) pixel near it. At about 2.4 s, id 4 (rare) looks the same plus a (255, 220, 240) 2 × 2 square whose top-left pixel is 3 px right of and 3 px below the crystal's top-left corner. Source: drifters/04-coin.md, crystal_size, palette, placeholder_look; scope report DRA-62, Not in GDD (rare glint); systems/drifters.md, Presentation, Coin.
- **It moves with the world (coin mode, `?debug=1`, hold ArrowUp):** two canvas reads 0.5 s apart while id 3 is on screen (about 1.6 s and 2.1 s) show it 33 px lower at the same x; its label reads `x 440.00` in both. Source: drifters/04-coin.md, kind (locked), rule 3; 03-world-and-camera.md, rule 9.
- **Collected (coin mode, `?debug=1`, hold ArrowUp from play start):** about 3.13 s after play start (tick 188): `drifter touch id=1 type=coin effect=collect`, then `drifter gone id=1 type=coin x=320.00 y=163.80`, and no `life lost`. From the next frame no crystal pixel of id 1 is drawn, and SCORE reads 50 more than the meters flown (`SCORE 67` around tick 188: 17 m + 50). ids 5 and 9 (row 1 again) do the same on ticks 339 and 519 (about 5.65 s and 8.65 s), each `y=163.80`, each adding 50. Source: drifters/04-coin.md, rule 4; 06-scoring.md, rule 2; systems/run.md, Rules, step 5a and Score.
- **The popup (same run as Collected):** on the first frame after id 1's collect, pink (255, 80, 150) text matching reference text `+50` at 16 px in that color, centered near (320, 164), its lower rows behind the ship's top. About 0.5 s later the same text is centered near (320, 149): it rose about 15 px and did not move down with the stars. About 1.1 s after the collect, no (255, 80, 150) pixel lies in x 290 to 350, rows 110 to 175: it is gone, all at once, with no fading frames between. Source: drifters/04-coin.md, popup, popup_color; scope report DRA-62, Limits; systems/run.md, Presentation, Points popup.
- **The respawn wait, and a press (coin mode, `?debug=1`, no key held until said):** the ship falls on tick 64 and waits at (320, 240). As soon as `drifter spawn id=4 type=coin variant=rare x=320.00 y=230.00` shows (about 2.27 s), tap ArrowLeft once: the log shows `respawn wait end`, then on the same tick `drifter touch id=4 type=coin effect=collect` and `drifter gone id=4 type=coin x=320.00 y=<y>` with `<y>` from 231.10 to 260.80 (it overlaps the waiting ship until tick 164). A pink `+100` (reference text at 16 px) rises from there, and SCORE gains 100. Keep every key released: the ship falls again (`life lost lives=1`) and waits at (320, 240). From about 3.98 s to 4.6 s (ticks 239 to 276) id 1 scrolls over the waiting ship: no `drifter touch` line for it. It keeps going and logs `drifter gone id=1 type=coin x=320.00 y=490.50` at about 8.1 s (tick 485). Source: drifters/04-coin.md, rule 4 and Edge cases (respawn wait); 05-lives-and-damage.md, rule 2.5; systems/run.md, Rules, step 5a.
- **Every row leaves (coin mode, `?debug=1`, hold ArrowUp from play start for about 9 s):** no `life lost`, no game over. `drifter gone id=3 type=coin x=440.00 y=490.50` (about 5.77 s, tick 346), `id=4 ... x=320.00 y=490.70` (about 6.22 s, tick 373), `id=2 ... x=200.00 y=490.50` (about 8.35 s, tick 501), `id=7 ... x=440.00 y=490.50` (about 8.77 s, tick 526). Each of those logs only `drifter spawn` and `drifter gone`. Only ids 1, 5 and 9 log `drifter touch`. On the frame before each `drifter gone`, that coin's last pixels are still on the bottom rows; on the frame after, none. Source: drifters/04-coin.md, rule 5; 07-drifters.md, rule 12; systems/drifters.md, Diagram (coin timeline).
- **Outlines (coin mode, `?debug=1`):** while id 3 is on screen, a green (0, 255, 0) 1 px box outline 12 px wide and 10 px tall sits on the crystal's middle, and no second, wider outline surrounds it: a coin has no graze zone. Its label under the crystal reads `coin common x 440.00 y <y> active`; id 4's reads `coin rare x 320.00 y <y> active`. Source: systems/debug-overlay.md, Presentation; 10-ui.md, debug_overlay; drifters/04-coin.md, hitbox, graze.
- **Bad coin file and bad coin rows (desktop, headless, `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`):** no code change. In a scratch copy of `game/tuning/`, set `"popup_ticks": 0` in `drifters/coin.json`. Point `app.tuning.TUNING_DIR` at it and call `run()`. The log shows ERROR `unexpected error, showing the error screen` with a `ValueError` naming `tuning/drifters/coin.json` and `popup_ticks`. Repeat with the file as committed and, one at a time, these rows added to `debug_spawns.json`: `{"type": "coin", "x": 100, "speed": 1.5}` (message: `rows[<i>]` and `coin has no speed`), `{"type": "coin"}` (`coin placement needs x`), `{"type": "coin", "x": 100, "invert": true}` (`coin has no invert`). No `error screen failed` line. Source: this contract, Rules, Tuning loader and Debug test spawn list; systems/drifters.md, Rules, Spawner and Coin.
- **Package contents:** as for DRA-61, and `core/popup.py`, `core/drifters/coin.py`, `ui/drifters/coin_view.py`, `ui/popup_view.py` and `tuning/drifters/coin.json` must be in `game.apk`.

## Impact
DRA-39 changes this frozen contract (v6). The tuning loader reads `hazards.json` and the satellite's own fields; the debug test spawn list moves from code into `game/tuning/debug_spawns.json`, with two modes and an editable loop length; `debug_spawns_due` takes the loaded list. The DRA-29 "Tuning loaded" check is reworded for the longer log line. Every file in `game/` that depends on it, found by grepping `game/` (tests included) for `load_tuning`, `debug_spawns`, `DEBUG_SPAWN`, `TUNING_DIR`, `frame_loop`, `add_drifters` and `pygbag`:

| File | Change needed |
|---|---|
| `game/app/tuning.py` | `HAZARDS_FILE`, the hazards checks and `HazardRules`, the satellite schema and `SatelliteVariantExtra`, the longer log line. Integration Engineer. |
| `game/app/debug_spawns.py` | rewritten: `SPAWN_LIST_FILE`, `ALL_ROWS`, `DEFAULT_MODE`, `DEFAULT_LOOP_TICKS`, `DebugSpawnList`, `load_debug_spawns`, the new `debug_spawns_due`; `DEBUG_SPAWN_PERIOD` and `DEBUG_SPAWNS` go. Integration Engineer. |
| `game/app/frame.py` | `spawn_list = load_debug_spawns(tuning)` in debug mode before `start_run()`; `debug_spawns_due(spawn_list, ...)` in the tick. Integration Engineer. |
| `game/app/loop.py`, `game/app/guard.py`, `game/app/mode.py`, `game/app/log.py`, `game/app/settings.py`, `game/main.py`, `game/scripts/start-driftward-ace.sh` | none. |
| `pygbag.ini` | none expected: `tuning/` and `.json` files are already packed. The DRA-39 package check confirms it. |
| `game/ui/look.py`, `game/ui/error_screen.py`, `game/tests/ui/test_error_screen.py` | none. |
| `game/tests/` | none: `check.sh` runs no `app` tests. |

All app changes are the Integration Engineer's, during DRA-39 integration. No task file. Until then, once `DrifterType.SATELLITE` exists (task DRA-39-03), the game stops at startup with the error screen, because the DRA-29 loader rejects `satellite.json`. Tests are not affected.

DRA-47 changes this contract on top of DRA-39 (not closed out, still `draft` at v6). The tuning loader reads `chain_lightning.json` with its own schema and builds the chain lightning's records, reads `telegraph_min` from `hazards.json`, and logs it. The spawn list module is unchanged in code; its rows and mode now include the chain lightning, and the committed file gains eight example rows. Grepping `game/` (tests included) for `load_tuning`, `_check_inside`, `Shape`, `HazardRules(`, `DrifterTypeTuning(`, `debug_spawns` and `frame_loop`:

| File | Change needed |
|---|---|
| `game/app/tuning.py` | the chain lightning's checks and records, `telegraph_min`, the longer log line; `_check_inside` and any other branch that reads a non-circle as a box must not see a `Line` (mypy fails there once `Shape` gains `Line`, task DRA-47-01). Integration Engineer. |
| `game/app/debug_spawns.py`, `game/app/frame.py` | none. |
| `game/tuning/drifters/chain_lightning.json` (new), `game/tuning/debug_spawns.json`, `game/tuning/hazards.json` | content, by whoever the Director names: the new file to its schema with the drifters.md values; the eight rows above; `telegraph_min` may be added or left out. |
| `game/app/loop.py`, `guard.py`, `mode.py`, `log.py`, `settings.py`, `game/main.py`, `game/scripts/`, `pygbag.ini` | none. |
| `game/tests/` | none from this contract. |

Until integration, once `DrifterType.CHAIN_LIGHTNING` exists (task DRA-47-03), the game stops at startup with the error screen: the loader has no rules for `chain_lightning.json`. Tests are not affected.

DRA-56 changes this frozen contract (v8). The tuning loader reads `fireball.json` with its own schema and builds the fireball's records; the spawn list accepts a row with neither `x` nor `y`, and the committed file gains six fireball rows; the earlier checks are reworded for the longer `tuning loaded` line and the new colors. Grepping `game/` (tests included) for `load_tuning`, `_load_drifter`, `_check_inside`, `DrifterTypeTuning(`, `debug_spawns`, `needs x or y` and `frame_loop`:

| File | Change needed |
|---|---|
| `game/app/tuning.py` | the fireball's checks and records, built with `FireballTypeExtra` and `fireball_hitbox`; the footprint check is not run on them. Integration Engineer. |
| `game/app/debug_spawns.py` | drop the "needs x or y" row check; the load-time spawn reports a missing coordinate. Integration Engineer. |
| `game/app/frame.py`, `loop.py`, `guard.py`, `mode.py`, `log.py`, `settings.py`, `game/main.py`, `game/scripts/`, `pygbag.ini` | none. |
| `game/tuning/drifters/fireball.json` (new), `game/tuning/debug_spawns.json` | content, by whoever the Director names: the new file to its schema with the values in `systems/drifters.md`, Rules, Tuning files; the six rows above. |
| `game/tests/` | none from this contract. |

Until integration, once `DrifterType.FIREBALL` exists (task DRA-56-01), the game stops at startup with the error screen: the loader has no rules for `fireball.json`. Tests are not affected.

DRA-61 changes this frozen contract (v9). The frame loop passes the final score to the Game Over box; the earlier checks that read the meters readout are reworded for SCORE. Grepping `game/` (tests included) for `draw_game_over`, `draw_hud` and `frame_loop`:

| File | Change needed |
|---|---|
| `game/app/frame.py` | imports `draw_final_score` and calls `draw_final_score(surface, run.score)` right after `draw_game_over(surface)`; the `_draw` docstring names the score. Integration Engineer. |
| `game/app/loop.py`, `guard.py`, `mode.py`, `log.py`, `settings.py`, `tuning.py`, `debug_spawns.py`, `game/main.py`, `game/scripts/`, `pygbag.ini` | none. `pygbag.ini` already packs every `ui/*.py`. |
| `game/tuning/` | none. |
| `game/tests/` | none from this contract. |

Until integration, `draw_game_over(surface)` keeps its signature, so the existing call in `game/app/frame.py` stays valid. Every `game/tests/check.sh` step passes, typecheck included, and the game never shows the error screen at game over. After task DRA-61-03 and before integration, the box shows the title and the prompt with the score line's place empty between them.

DRA-62 changes this frozen contract (v10). The tuning loader reads `coin.json` with its own schema and builds the coin's records; the frame draws the points popups after the drifters; the committed spawn list gains four coin rows; the earlier checks are reworded for the longer `tuning loaded` line and the coin colors. Grepping `game/` (tests included) for `load_tuning`, `_load_drifter`, `DrifterTypeTuning(`, `debug_spawns`, `render_drifter` and `frame_loop`:

| File | Change needed |
|---|---|
| `game/app/tuning.py` | the coin's checks and records, built with `CoinVariantExtra`, `CoinTypeExtra` and `coin_hitbox`. Integration Engineer. |
| `game/app/frame.py` | imports `draw_points_popup` and draws every popup right after the drifters; the `_draw` docstring names them. Integration Engineer. |
| `game/app/debug_spawns.py`, `loop.py`, `guard.py`, `mode.py`, `log.py`, `settings.py`, `game/main.py`, `game/scripts/`, `pygbag.ini` | none. `pygbag.ini` already packs every `core/`, `ui/` and `tuning/` file. |
| `game/tuning/drifters/coin.json` (new), `game/tuning/debug_spawns.json` | content, by whoever the Director names: the new file to its schema with the values in `systems/drifters.md`, Rules, Tuning files; the four rows above. |
| `game/tests/` | none from this contract. |

Until integration, once `DrifterType.COIN` exists (task DRA-62-01), the game stops at startup with the error screen: the loader has no rules for `coin.json`. Tests are not affected. Popups exist in core from task DRA-62-02 but are not drawn until integration.

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
- **The scroll starts right after the spawn (DRA-13).** The control card doesn't exist yet, so the Director set play start to the moment the ship first appears at screen center. Calling `start_scroll()` next to `spawn()`, before the first frame, makes tick 0 the state the first frame shows. From DRA-23 `core.run.start_run()` makes both calls.
- **Dropped catch-up time doesn't scroll (DRA-13).** Distance counts ticks the game ran. Time the cap drops is never run, so the world doesn't jump ahead after a hidden tab, the same as the ship.
- **The HUD is drawn last (DRA-13).** 10-ui.md, rule 1 puts the HUD on top of everything. The overlay and the HUD never overlap, so moving the overlay from last to second-to-last changes no pixel today.
- **The cap logs only when it starts.** A slow device can hit the cap every frame. Logging each time would be a line per frame, which the log policy forbids.
- **Browser logs go to `console.log`.** In pygbag 0.9.3, stdout and stderr reach only its hidden terminal, never the devtools console. Writing through `platform.window.console.log` makes the start line visible, as the scope report promises. Every level uses `console.log`, not `console.warn` or `console.error`, as the Director decided (D2). Desktop keeps stdout, so the level is still readable from the line text.
- **The PEP 723 block in `main.py`.** pygbag reads only `main.py` to pick the packages it installs. `main.py` imports only `asyncio` and `app.loop`, so the block is what gets pygame-ce into the browser build (D1). It is metadata only, with no logic and no import, so `main.py` stays a thin entry point.
- **The guard removes null characters, the view doesn't (DRA-19).** pygame's font render raises on a string with `\x00` in it. Before DRA-19 that made the guard log "error screen failed" and leave the last frame up, so a debug-mode player saw no error screen for that message. The guard already shapes `detail` into one line, so it is the one place that turns an exception into displayable text. Removing the character, not replacing it, keeps the rest of the message as it was. The full message with the null stays in the logged traceback (10-ui.md, error_debug_line).
- **The app holds one `Run` (DRA-23).** Game over freezes the ship and the scroll together, and a retry resets them together. Those are game rules, so they live in core. The app keeps one state, calls one step per tick, and only decides what to draw from the run's fields.
- **The app skips `draw_ship` while the ship blinks hidden (DRA-23).** `run.ship_visible` is the core fact; the app reads it and doesn't call the view, the same way it calls the overlay only while `overlay_visible`. The ship view stays unchanged.
- **The app passes `run.score` to the Game Over box's score line, a call of its own (DRA-61).** The box stays free of core, as in DRA-23, and the app already reads the run's fields to decide what to draw. A second call, not a new argument, keeps the existing `draw_game_over(surface)` call valid through the build, so QA stays clean before integration (Director, DRA-61 revision: "keep QA clean"). The HUD keeps taking the run, so its call doesn't change.
- **The Game Over box is drawn before the HUD (DRA-23).** 10-ui.md, rule 1 puts the HUD on top of everything. The box is in the middle of the screen and the HUD at the top, so they never overlap, and the HUD stays the last call.
- **The DRA-6 and DRA-13 checks are reworded, not dropped (DRA-23).** They relied on the ship respawning once a second with no key held. The behavior they check (one line per event, the cap, the readout rate) still holds; only the way to see it changes.
- **The tuning is loaded in the app and checked by hand (DRA-29).** The Director decided the app loads and validates the files once and core never reads files. game/CONTEXT.md puts validation at the edge. A JSON Schema library would need packages pygbag can't install, so the loader checks the schema's rules itself and the schema stays the written rule both sides follow.
- **The tuning is loaded in both modes (DRA-29).** Game rules are the same in both modes, and waves will need it in normal mode. A bad file then breaks both modes the same way, before the first frame.
- **`TUNING_DIR` from `__file__` (DRA-29).** pygbag runs the game from its own folder in the browser; a path built from the module's own place works the same on desktop and in the browser. It is a module constant read at call time so the bad-file check can point it at a scratch folder without a code change.
- **The debug list counts `run.scroll.ticks` (DRA-29).** It is the run's own play time: it freezes at game over and restarts at 0 on a retry, so the list does both with no state of its own. `add_drifters` does nothing at game over, so calling it on frozen ticks never adds a drifter twice.
- **The first test meteorite on tick 1 (DRA-29).** The scope gives the order, the spacing and the repeat, not the first tick. Tick 1 is the first tick of play, so the list starts when play starts. It is a debug stand-in; the Director may shift it.
- **The spawn list is a file in `game/tuning/` (DRA-39).** The Director edits it by hand, and the folder is already packed into the build and read through `TUNING_DIR`, so the bad-file checks can point it at a scratch copy. It is still not a tuning value or a wave: only debug mode reads it.
- **Rows carry no time; they are spread evenly over the loop (DRA-39).** The Director asked for rows with only a type and a position, and a loop whose length can be changed. Spreading the rows in play evenly over one loop needs no time field, keeps the DRA-29 meteorite timing exactly (three rows in 180 ticks: 0, 60, 120), and still works when a mode leaves only some rows in play. A row that needs its own time would be a new field for the Director to approve.
- **Every row is spawned once at load (DRA-39).** Only the drifter knows which coordinate it needs, which variants it has and whether it takes `invert`. Spawning each row once through the real spawner checks all of that with core's own rules and fails at startup, naming the row, instead of mid-run. The spawner is pure, so the throw-away drifters change nothing.
- **Rows out of play are checked too (DRA-39).** Switching the mode should never reveal a broken row that was hidden before.
- **Normal mode never reads the list (DRA-39).** Debug mode adds the list and nothing else (15-tech-constraints.md, rule 7). A hand-edited debug file must not be able to stop the game for players.
- **`hazards.json` must exist, its fields may be left out (DRA-39).** The scope asks that none of the values be required. A missing file still raises, like every other data file, so a broken package shows at once instead of silently using defaults. `{}` is a valid file.
- **The defaults live in core, not in the loader (DRA-39).** `core.drifters.base` holds `DEFAULT_REHIT_COOLDOWN_TICKS` and `DEFAULT_REHIT_DIM` with their GDD sources. The loader fills left-out fields from them, so the numbers have one home.
- **The earlier debug checks are reworded, not dropped (DRA-29).** The test spawn list drops a medium meteorite on the respawn column every 3 s, so a waiting ship gets hit in debug mode. The rules the old checks test still hold; only what else shows up in the log, and how long a wait can last before a hit, changes. Normal-mode checks are untouched.
- **The loader builds the chain's hitbox with core's functions (DRA-47).** The chain lightning's width, height and hitbox follow from its nodes. Calling `layout_size` and `chain_hitbox` from `core.drifters.chain_lightning` keeps that rule in one place, the same one `born` uses after mirroring, instead of a copy in the app.
- **One example row per variant, and one that meets the ship (DRA-47).** The scope asks for example rows for every variant. Seven rows sit clear of the ship's column, so the checks can read each one alone; row 1 is the default variant with a slower `speed` so its first fire lands on the waiting ship, which shows in the browser both that a charge never hits and that the fire does. The triangle appears twice to show `invert`.
- **The loader builds the fireball's hitbox with core's function (DRA-56).** Its tail's place follows from the head, `tail_ratio` and the angle, so `fireball_hitbox` from `core.drifters.fireball` is the one home of that rule, the same one `born` uses with `invert`.
- **A spawn row may have no position (DRA-56).** The scope gives the fireball a default corner entry, which is a row with neither `x` nor `y`. Only the drifter knows which coordinate it needs, and the load-time spawn already asks it, so the loader's own "x or y" check would only refuse a valid fireball row.
- **Fireball rows: one meets the ship, five don't (DRA-56).** The scope asks for both variants, both directions and all three entries. Row 1's x 125 puts its path through the foot of a ship waiting at the respawn point and 15 px clear of a ship held on the top line, so one page shows the hit and another shows every row leave untouched. Row 6 carries `speed`, so the debug field is seen working.
- **Idle after the error, don't exit.** Ending `run()` hands control back to pygbag in a state we haven't tested. Idling keeps the canvas showing the error screen and keeps the page responsive.
- **The error screen is tested headless.** A browser run can't trigger an unexpected error without a debug-only trigger, and that would be new scope. Task DRA-5-02 proves the screen draws right in both modes.
- **Run-mode parsing has no permanent test.** It lives in `game/app/`, and `game/tests/check.sh` runs only `tests/core` and `tests/ui`. Only the Director can add an `app` step. The integration browser run covers the three cases (Rules, Integration checks, Run modes).
- **`?debug=1` and pygbag.** pygbag's page reads some URL parts for its own options. The Integration Engineer checks that `?debug=1` reaches Python unchanged and doesn't switch pygbag into a mode of its own. If it does, that is a blocked report: the switch value is locked in the GDD.
