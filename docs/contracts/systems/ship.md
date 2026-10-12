# Ship
Version: 3
Status: frozen
Features: DRA-6, DRA-13, DRA-19
Created by: architect

## Purpose
The ship's state and its one-tick physics step: thrust, gravity, drag, fall cap, move, side walls, top line. One temporary stand-in ends the tick: the floor respawn, until lives exist. Plus the view that draws the ship as its placeholder rectangle.

From DRA-13 the top-line stop is the real rule, not a stand-in: the screen is fixed and the top line is a ceiling (03-world-and-camera.md, rule 2; 04-ship.md, rule 2, step 7). Its behavior doesn't change. The world scroll never touches the ship (`docs/contracts/systems/scroll.md`).

Who builds what:
- `game/core/ship.py`: the Gameplay Implementer, task `DRA-6-01-gameplay-implementer`. Field docs, `Final` and `slots` in DRA-19: task `DRA-19-01-gameplay-implementer`.
- `game/ui/ship_view.py`: the UI Developer, task `DRA-6-02-ui-developer`.
- `game/tests/core/test_ship.py`: the QA Engineer, task `DRA-6-03-qa-engineer`.
- Calling `step` once per tick and building `Thrust` from the keys: the Integration Engineer, in `game/app/frame.py`, from `docs/contracts/systems/app.md`.

## Diagram
```mermaid
flowchart TD
  IN["Ship + Thrust"] --> T1["1 thrust<br/>left: vx -= THRUST_SIDE, right: vx += THRUST_SIDE<br/>up: vy -= THRUST_UP, down: vy += THRUST_DOWN"]
  T1 --> T2["2 gravity<br/>vy += GRAVITY"]
  T2 --> T3["3 drag<br/>vx *= DRAG_X"]
  T3 --> T4["4 fall cap<br/>vy = min(vy, FALL_CAP)"]
  T4 --> T5["5 move<br/>x += vx, y += vy"]
  T5 --> T6{"6 side walls<br/>edge past a wall?"}
  T6 -- yes --> W["clamp edge to wall, vx = 0<br/>wall = side"]
  T6 -- no --> WN["wall = None"]
  W --> T7
  WN --> T7{"7 top line, ceiling<br/>top edge above TOP_LINE_Y?"}
  T7 -- yes --> TL["top edge = TOP_LINE_Y, vy = 0<br/>at_top_line = True"]
  T7 -- no --> TN["at_top_line = False"]
  TL --> T8
  TN --> T8{"8 floor, TEMPORARY<br/>top edge >= SCREEN_H?"}
  T8 -- yes --> R["respawn: spawn() at rest"]
  T8 -- no --> OUT["new Ship"]
  R --> OUT
```

```mermaid
flowchart LR
  APP["app.frame"] -- "Thrust, once per frame" --> STEP["core.ship.step"]
  STEP -- "Ship" --> APP
  APP -- "Ship" --> VIEW["ui.ship_view.draw_ship"]
  VIEW -. reads .-> C["core.ship: SHIP_W, SHIP_H"]
```

## Interface
```python
# game/core/ship.py
# Imports: stdlib, core.world. Never pygame, ui or app.
# Every module-level constant is typing.Final (DRA-19).

SHIP_W: Final[int] = 32               # 04-ship.md, ship_w (guess)
SHIP_H: Final[int] = 32               # 04-ship.md, ship_h (guess)
GRAVITY: Final[float] = 0.16          # 04-ship.md, gravity, px/tick² (guess)
THRUST_SIDE: Final[float] = 0.42      # 04-ship.md, thrust_side, px/tick² (guess)
THRUST_UP: Final[float] = 0.42        # 04-ship.md, thrust_up, px/tick² (guess)
THRUST_DOWN: Final[float] = 0.42      # 04-ship.md, thrust_down, px/tick² (guess)
DRAG_X: Final[float] = 0.94           # 04-ship.md, drag_x, × per tick (guess)
FALL_CAP: Final[float] = 5.5          # 04-ship.md, fall_cap, px/tick (guess)
SPAWN_X: Final[float] = 320.0         # 03-world-and-camera.md ship_start = 05-lives-and-damage.md fall_respawn
SPAWN_Y: Final[float] = 240.0         # same

Wall = Literal["left", "right"]       # a type alias, not a constant: no Final

@dataclass(frozen=True, slots=True)
class Thrust:
    """Which arrow keys are held this tick."""
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False

@dataclass(frozen=True, slots=True)
class Ship:
    """Ship state after a tick. Screen px, y down."""
    x: float                       # center x
    y: float                       # center y
    vx: float                      # px/tick, + is right
    vy: float                      # px/tick, + is down (falling)
    wall: Wall | None = None       # wall the ship was clamped against this tick
    at_top_line: bool = False      # the top line (ceiling) clamped the ship this tick

def spawn() -> Ship: ...
    # Ship at (SPAWN_X, SPAWN_Y), vx = vy = 0, wall None, at_top_line False.

def step(ship: Ship, thrust: Thrust) -> Ship: ...
    # One 60 Hz tick. Pure apart from event logging: same ship and thrust in,
    # same ship out. Never mutates its input.
```
Derived edges, used by the rules below: left edge `x - SHIP_W / 2`, right edge `x + SHIP_W / 2`, top edge `y - SHIP_H / 2`.

The code carries each `Ship` field's comment above (what it is, its unit, its sign) as that field's documentation, together with the class docstring's "Screen px, y down". From DRA-19. Source: scope report DRA-19, item 1; review DRA-6-01-gameplay-implementer, finding 1.

```python
# game/ui/ship_view.py
# Imports: pygame, core.ship. Never app.
SHIP_COLOR: tuple[int, int, int] = (255, 255, 255)   # 04-ship.md, placeholder_look (guess)

def draw_ship(surface: pygame.Surface, ship: Ship) -> None: ...
```

## Presentation
`draw_ship` reads only these core fields and constants. It draws on top of what is there and never fills the background.

| Core field | Shown as |
|---|---|
| `ship.x`, `ship.y` | the center of the ship rectangle. Its top-left corner is `(round(ship.x - SHIP_W / 2), round(ship.y - SHIP_H / 2))`. Source: 04-ship.md, placeholder_look; 03-world-and-camera.md, ship_start (screen center) |
| `SHIP_W`, `SHIP_H` | the rectangle's size, 32 × 32. Source: 04-ship.md, ship_w, ship_h (guess) |
| (always) | filled, color `SHIP_COLOR`, (255, 255, 255). Source: 04-ship.md, placeholder_look (guess) |

- `vx`, `vy`, `wall` and `at_top_line` are not shown by the ship view. The debug overlay shows `vx` and `vy` (`docs/contracts/systems/debug-overlay.md`).
- A ship partly past the floor is drawn as is. pygame clips what falls outside the surface.
- The view only draws. It never flips, never logs per frame, never catches an error, never changes the ship.

## Rules
Values:
- Every constant above has its value and source on its line. All are `guess` in the GDD except `fall_respawn`, which is locked. Source: 04-ship.md, 03-world-and-camera.md and 05-lives-and-damage.md, Values. Scope report DRA-6, Values needed.

The step, in this order, every tick. Source: 04-ship.md, rule 2:
1. **Thrust.** `left` subtracts `THRUST_SIDE` from `vx`, `right` adds it. `up` subtracts `THRUST_UP` from `vy`, `down` adds `THRUST_DOWN`. Opposite keys held together cancel. Source: 04-ship.md, rule 2.1 and Edge cases.
2. **Gravity.** `vy += GRAVITY`. Always, whatever is held. Source: 04-ship.md, rule 2.2; 01-vision.md, locked decision 4.
3. **Drag.** `vx *= DRAG_X`. No drag on `vy`. Source: 04-ship.md, rules 2.3 and 7.
4. **Fall cap.** If `vy > FALL_CAP`, `vy = FALL_CAP`. No cap on upward speed. Source: 04-ship.md, rules 2.4 and 7.
5. **Move.** `x += vx`, `y += vy`. Source: 04-ship.md, rule 2.5.
6. **Side walls.** If the left edge is below 0: set the left edge to 0, `vx = 0`, `wall = "left"`. If the right edge is past `SCREEN_W`: set the right edge to `SCREEN_W`, `vx = 0`, `wall = "right"`. Otherwise `wall = None`. No bounce. Source: 03-world-and-camera.md, rule 6; 01-vision.md, locked decision 3; 04-ship.md, rule 2.6.
7. **Top line, a ceiling.** If the top edge is above `TOP_LINE_Y` (`y - SHIP_H / 2 < TOP_LINE_Y`): set the top edge to `TOP_LINE_Y`, `vy = 0`, `at_top_line = True`. Otherwise `at_top_line = False`. Permanent from DRA-13. Source: 03-world-and-camera.md, rule 2 (a ceiling; the top edge is the point that counts); 04-ship.md, rule 2, step 7; 91-decision-log.md, row 22; scope report DRA-13, Limits.
8. **Floor, TEMPORARY.** If the ship is fully below the floor (`y - SHIP_H / 2 >= SCREEN_H`): return `spawn()`. No life is lost, nothing else happens. The world scroll and the distance keep going through it. Source: scope report DRA-6, Limits (temporary build rule, approved by the Director); scope report DRA-13, Limits (kept as is); 03-world-and-camera.md, rules 4 and 5; 05-lives-and-damage.md, fall_respawn. Replaced when lives exist.

Other rules:
- Every tick runs every step. Nothing pauses the physics or the input. Source: 04-ship.md, rule 3.
- Input only changes acceleration. No key sets a speed or a position. The wall clamp, the top-line stop and the respawn are rules, not input. Source: 04-ship.md, rule 4; 01-vision.md, Pillar 1.
- The run starts with `spawn()`: (320, 240), at rest. Source: 03-world-and-camera.md, ship_start (guess).
- `step` uses no frame time and no randomness. Same input, same output. Source: 15-tech-constraints.md, rule 2.
- Core behaves the same in normal and debug mode. It never reads the run mode. Source: game/CONTEXT.md, Run modes; 15-tech-constraints.md, rule 7.
- Core never imports pygame, `ui` or `app`. Source: game/CONTEXT.md, Layout.
- The ship never reads the world scroll, and the scroll never changes the ship. `step` takes no scroll. Source: 03-world-and-camera.md, rule 4; systems/scroll.md.

Logging (logger `core.ship`, DEBUG, by event, never by tick). Source: game/CONTEXT.md, Logging; 15-tech-constraints.md, rule 9. The wall and top-line wording ("the ship after the clamps, before any respawn") is from DRA-19 and matches the code; no log line changes. Source: scope report DRA-19, item 2; review DRA-6-01-gameplay-implementer, finding 2:
- `wall hit side=%s x=%.2f y=%.2f`: when the ship after the clamps, before any respawn, has `wall` set and the input ship's `wall` was different. Holding a key against a wall logs once, not every tick.
- `top line stop x=%.2f y=%.2f`: when the ship after the clamps, before any respawn, has `at_top_line` True and the input ship had it False. Holding Up at the line logs once.
- `respawn from x=%.2f y=%.2f`: on every respawn, with the position the ship fell from (after step 5 and the clamps, before the reset).
- Values are the new position after the clamp. Nothing else is logged. No line on a tick where nothing happened.
- If the ship hits a wall and falls off the floor in the same tick, the wall line comes first, then the respawn line.

## Impact
DRA-19 changes this frozen contract (v2). No behavior, signature, value or log line changes. Constants gain `Final`, `Thrust` and `Ship` gain `slots=True`, the code documents each `Ship` field, and the Logging wording is fixed to match the code. Every file in `game/` that depends on it, found by grepping `game/` (tests included) for `core.ship`, `Ship`, `Thrust`, `__dict__`, `__slots__`, `setattr`, `vars(` and the constant names:

| File | Change needed |
|---|---|
| `game/core/ship.py` | `Final[...]` on the ten constants, `slots=True` on `Thrust` and `Ship`, a doc for each `Ship` field. Task `DRA-19-01-gameplay-implementer`. |
| `game/ui/ship_view.py` | none. It reads `SHIP_W`, `SHIP_H`, `ship.x`, `ship.y`, which keep their names, types and values. |
| `game/ui/debug_overlay.py` | none from this contract. See `systems/debug-overlay.md`. |
| `game/app/frame.py` | none. It builds `Thrust` with keywords and replaces `ship` each tick; neither needs a `__dict__`. |
| `game/tests/core/test_ship.py`, `game/tests/ui/test_hud.py` | none. They build `Ship` and `Thrust` with keywords and read fields. No test sets an attribute, reads `__dict__` or patches a constant. |

## Rationale
- **The top-line stop stays as built.** The GDD now makes the top line a ceiling with the same clamp and `vy = 0` that DRA-6 built as a stand-in (91-decision-log.md, row 22). Only its label changes. The floor respawn is still a stand-in: the GDD's fall costs a life, and lives are out of DRA-13.
- **`x`, `y` are the ship's center.** The GDD puts `ship_start` and `fall_respawn` at "screen center (320, 240)", and the scope says the ship starts at screen center. With center coordinates the overlay shows exactly 320 and 240 at the start, the same numbers the GDD uses.
- **`step` returns a new frozen `Ship`.** A pure step is easy to test and to repeat. DRA-5 reserved `state = core_step(state, held_input)` in the loop.
- **`wall` and `at_top_line` live in the state.** The log policy forbids a line every tick, but holding a key against a wall clamps every tick. Keeping the last tick's contact lets `step` log only when contact starts. They are also the facts a later feature (lava walls) will need.
- **Fully below the floor is `top edge >= SCREEN_H`.** With the top edge at 480 the ship covers rows 480 to 511. No pixel of it is on the 480-row screen, so it is fully below the floor (03, rule 5).
- **The top-line clamp triggers only when the edge is past the line.** A ship resting exactly on the line with no upward speed isn't "hitting" it. So `vy = 0` and the log happen when the ship actually pushes past.
- **Physics constants live in `core/ship.py`.** The tuning file is out of DRA-6 scope. When the Tuning Engineer's file exists, a later contract moves these values to it, with a schema.
- **No art task.** The ship is a new entity type, but the scope rules out sprite art and the thrust flame. The placeholder rectangle needs no asset.
- **The view rounds the corner with `round`.** pygame draws on whole pixels. Rounding the corner, not the center, keeps the rectangle exactly 32 × 32.
- **The ship color lives in `ship_view.py`, not `ui/look.py`.** Only the ship view uses it. `look.py` holds values shared by several views.
- **`Final[int]` and `Final[float]`, not bare `Final` (DRA-19).** The Interface has always stated each constant's type. Keeping it inside `Final` keeps that text and the code the same. `Final` changes nothing at run time; it tells a reader and a type checker that the value is never reassigned.
- **`slots=True` on both dataclasses (DRA-19).** Both are small frozen records built thousands of times a run. Slots make them lighter and stop stray attributes. Nothing in `game/` reads their `__dict__`, so it fits. Fields stay as they are.
- **Logging wording names the pre-respawn ship (DRA-19).** After a respawn the returned ship is `spawn()`, with `wall` None and `at_top_line` False. So "the returned ship" could never log a wall hit on a respawn tick, yet the same section says the wall line comes before the respawn line. The code reads the ship after the clamps, before the respawn. The wording now says that.
