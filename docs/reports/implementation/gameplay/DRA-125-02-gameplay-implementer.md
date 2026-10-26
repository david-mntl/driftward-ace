Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-125-02: build `core/game_flow.py`, the screens, the fresh-press rules, the pause, RETRY and MENU, and `add_flow_drifters` (Architect, `docs/contracts/DRA-125/tasks/DRA-125-02-gameplay-implementer.md`, contract `docs/contracts/systems/game-flow.md` version 0 and `systems/run.md`).

2. **Delivered:**
   - `game/core/game_flow.py` (new): `Screen`, `MenuItem`, `GameOverChoice`, `MENU_START_SELECTION`, `GAME_OVER_START_SELECTION`, `TickInput`, `GameFlow`, `start_flow`, `step_flow`, `add_flow_drifters`. The signatures and field names are the contract's.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/game_flow.py`: clean.
   - `game/tests/check.sh`: `lint` PASS (ruff check and format), `ui` PASS (65). `typecheck` FAIL with 7 errors, all `retry_armed` in test files (impact.md row DRA-125-01, cleared by DRA-125-09); `mypy --strict core/game_flow.py` alone: no issues. `core`: 26 failed, 3205 passed: the same 26 as after DRA-125-01 (the flow adds no failure). Nothing else fails.
   - Acceptance script below: every case behaves as the task lists (see Output notes). Run twice, output byte-identical (`cmp`).
   - Grep of `game/core/game_flow.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no hits.

4. **Assumptions:**
   - `PLAYING` entered with a run that is already `game_over` is not a reachable state (the flow only enters PLAYING from a menu Play, a resume or RETRY, each with a live run), so the step does not special-case it.
   - `Screen`, `MenuItem` and `GameOverChoice` values are the contract's strings.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-125/tasks/DRA-125-02-gameplay-implementer.md`. Left alone: `core/run.py` and `core/last_life.py` (DRA-125-01), every test (DRA-125-09), `game/ui/`, `game/app/` (Integration Engineer).

7. **Status:** done.

## Decisions
- One `match` on `flow.screen` calls one small function per screen; each gets `replace(flow, run_stepped=False)`, so `run_stepped` is True only where `step_run` sets it. After the match, `confirm_held` and `arrows_held` are stored from the keys on every path (contract, Presses).
- `_moved` is one generic wrap-around move (`[E: Enum]`, Python 3.12) for both selections: down minus up, so an up and a down press on one tick cancel out. A confirm press returns before any move, so arrows on that tick never move the selection (contract, Presses).
- Log order: `next_run` and `step_run` log inside the screen function, before the flow's own `pause by=` and `screen ...` lines, as the contract asks. `pause by=` is `key` when a confirm press is present, else `focus`. Selection moves log only when the new member differs; resets on entering a screen log nothing.
- Entering MENU (from a page or GAME_OVER) goes through one helper that resets the selection to `MENU_START_SELECTION`. Entering GAME_OVER resets `game_over_selection` the same way.
- The last life (`run.last_life`) is checked before the pause test, so a confirm press or focus loss there reaches `step_run` and nothing else.
- Paused ticks call `hold_arrows` on the resume tick too, so the arrows held when play resumes are the ones the run holds.
- Sources: `MENU_START_SELECTION` Play (02-game-flow.md, menu_start_selection, guess); `GAME_OVER_START_SELECTION` RETRY (game_over_choices, locked). No other number.

## Acceptance script
Saved nowhere in the repo. Save it as a file outside `game/`, then from `game/`:
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <script file>`

The script prints a row on every tick that logs a line or changes the screen, a selection, `run_stepped`, `lives` or `waiting`, plus every row in the short scripted stretches. Long stretches of plain play print only those rows.

```python
"""DRA-125-02 acceptance run. From game/: PYTHONPATH=. python <this file>."""

import logging
import sys
from dataclasses import replace

from core.collision import Circle
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.game_flow import GameFlow, TickInput, add_flow_drifters, start_flow, step_flow
from core.run import start_run
from core.ship import Thrust

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("    LOG %(name)s %(levelname)s %(message)s"))
handler.addFilter(lambda r: r.name == "core.game_flow" or r.levelno >= logging.INFO)
for name in ("core.game_flow", "core.run"):
    logging.getLogger(name).setLevel(logging.DEBUG)
    logging.getLogger(name).addHandler(handler)

NONE = TickInput()
ENTER = TickInput(confirm=True)
UP = TickInput(thrust=Thrust(up=True))
DOWN = TickInput(thrust=Thrust(down=True))
FOCUS = TickInput(focus_lost=True)


class Counter(logging.Handler):
    count = 0

    def emit(self, record: logging.LogRecord) -> None:
        self.count += 1


counter = Counter()
for name in ("core.game_flow", "core.run"):
    logging.getLogger(name).addHandler(counter)

tick = 0
flow: GameFlow = start_flow(start_run())
last_key: tuple[object, ...] | None = None


def summary(f: GameFlow) -> str:
    return (
        f"screen={f.screen.value} menu={f.menu_selection.value} "
        f"over={f.game_over_selection.value} stepped={f.run_stepped} "
        f"ticks={f.run.scroll.ticks} lives={f.run.lives} waiting={f.run.waiting}"
    )


def feed(keys: TickInput, note: str = "", *, show: bool = True) -> None:
    global flow, tick, last_key
    before = counter.count
    flow = step_flow(flow, keys)
    tick += 1
    key = (flow.screen, flow.menu_selection, flow.game_over_selection, flow.run_stepped,
           flow.run.lives, flow.run.waiting)
    if show or counter.count != before or key != last_key:
        print(f"t={tick} {note:<18}{summary(flow)}")
    last_key = key


def play_until(stop, keys_for, note: str) -> None:
    while not stop(flow):
        feed(keys_for(flow), note, show=False)


def section(title: str) -> None:
    print(f"== {title}")


def into_play() -> None:
    """Fresh flow, release, press Enter on Play."""
    global flow
    flow = start_flow(start_run())
    feed(NONE, "release")
    feed(ENTER, "enter Play")
    feed(NONE, "release")


section("menu: up, up, down, down, down; Instructions; back; Leaderboard; back")
feed(NONE, "release (start held)")
for k, n in ((UP, "up"), (UP, "up"), (DOWN, "down"), (DOWN, "down"), (DOWN, "down")):
    feed(k, n)
    feed(NONE, "release")
feed(ENTER, "enter Instructions")
feed(TickInput(confirm=True, thrust=Thrust(down=True)), "enter+down held")
feed(NONE, "release")
feed(TickInput(confirm=True), "space back")
feed(NONE, "release")
feed(DOWN, "down")
feed(NONE, "release")
feed(DOWN, "down")
feed(NONE, "release")
feed(ENTER, "enter Leaderboard")
feed(NONE, "release")
feed(ENTER, "enter back")

section("Enter on Play held 40 ticks, released, pressed again, Space resumes")
flow = start_flow(start_run())
feed(NONE, "release")
feed(ENTER, "enter Play (press)")
for _ in range(40):
    feed(ENTER, "held", show=False)
feed(ENTER, "held (41st)")
feed(NONE, "released")
feed(ENTER, "enter again")
feed(NONE, "release (paused)")
feed(ENTER, "space resume")
feed(NONE, "release")

section("focus_lost: during play, during the pause, on the menu")
feed(FOCUS, "focus lost, play")
feed(FOCUS, "focus lost, pause")
feed(NONE, "paused, none")
flow = start_flow(start_run())
feed(NONE, "release")
feed(FOCUS, "focus lost, menu")

section("pause in a respawn wait, UP pressed in the pause and held after the resume")
into_play()
play_until(lambda f: f.run.waiting, lambda f: NONE, "fall")
feed(NONE, "waiting")
feed(ENTER, "enter: pause")
feed(UP, "UP pressed paused")
feed(UP, "UP held paused")
feed(TickInput(confirm=True, thrust=Thrust(up=True)), "enter: resume")
feed(UP, "resumed, UP held")
feed(UP, "UP held")
feed(NONE, "UP released")
feed(UP, "UP pressed")

section("last life: Enter and focus_lost do nothing; GAME_OVER; choices")
flow = start_flow(replace(start_run(), lives=1))
feed(NONE, "release")
feed(ENTER, "enter Play")
feed(NONE, "release")
play_until(lambda f: f.run.last_life, lambda f: NONE, "fall")
feed(ENTER, "enter in last life")
feed(NONE, "release")
feed(FOCUS, "focus in last life")
feed(NONE, "none")
play_until(lambda f: f.screen.value == "game_over", lambda f: NONE, "last life")
feed(NONE, "over, none")
feed(DOWN, "down")
feed(NONE, "release")
feed(DOWN, "down")
feed(NONE, "release")
feed(UP, "up")
feed(NONE, "release")
feed(ENTER, "enter MENU")
feed(NONE, "release")
feed(ENTER, "enter Play")
feed(NONE, "release")
section("lose again (3 lives), Enter on RETRY")


def arrows(f: GameFlow) -> TickInput:
    return UP if f.run.waiting else NONE


play_until(lambda f: f.screen.value == "game_over", arrows, "playing")
feed(ENTER, "enter RETRY")
feed(NONE, "release")

section("add_flow_drifters: paused, page, stepped")
tuning = DrifterTuning(
    drifters={
        DrifterType.METEORITE: DrifterTypeTuning(
            variants={"medium": VariantTuning(width=28.0, height=28.0, hitbox=(Circle(0, 0, 14.0),))},
            default_variant="medium",
            speed_ratio=1.0,
            entry_warning_ticks=60,
        )
    },
    switches=PlaytestSwitches(),
)
placement = (Placement(drifter_type=DrifterType.METEORITE, x=100.0, y=-50.0),)
for label, screen_keys in (("paused tick", ENTER), ("page tick", None), ("stepped tick", NONE)):
    if label == "page tick":
        flow = start_flow(start_run())
        feed(NONE, "release")
        feed(DOWN, "down")
        feed(NONE, "release")
        feed(ENTER, "enter Instructions")
    else:
        into_play()
        if screen_keys is ENTER:
            feed(ENTER, "enter: pause")
        else:
            feed(NONE, "play tick")
    added = add_flow_drifters(flow, placement, tuning)
    print(f"   {label}: screen={flow.screen.value} run_stepped={flow.run_stepped} "
          f"drifters {len(flow.run.drifters)} -> {len(added.run.drifters)} "
          f"next_uid {flow.run.next_uid} -> {added.run.next_uid}")
```

Output:

```
== menu: up, up, down, down, down; Instructions; back; Leaderboard; back
t=1 release (start held)screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select leaderboard
t=2 up                screen=menu menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
t=3 release           screen=menu menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select instructions
t=4 up                screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
t=5 release           screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select leaderboard
t=6 down              screen=menu menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
t=7 release           screen=menu menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select play
t=8 down              screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=9 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select instructions
t=10 down              screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
t=11 release           screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen instructions
t=12 enter Instructionsscreen=instructions menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
t=13 enter+down held   screen=instructions menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
t=14 release           screen=instructions menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen menu
t=15 space back        screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=16 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select instructions
t=17 down              screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
t=18 release           screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select leaderboard
t=19 down              screen=menu menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
t=20 release           screen=menu menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen leaderboard
t=21 enter Leaderboard screen=leaderboard menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
t=22 release           screen=leaderboard menu=leaderboard over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen menu
t=23 enter back        screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
== Enter on Play held 40 ticks, released, pressed again, Space resumes
t=24 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen playing
t=25 enter Play (press)screen=playing menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=26 held              screen=playing menu=play over=retry stepped=True ticks=1 lives=3 waiting=False
t=66 held (41st)       screen=playing menu=play over=retry stepped=True ticks=41 lives=3 waiting=False
t=67 released          screen=playing menu=play over=retry stepped=True ticks=42 lives=3 waiting=False
    LOG core.game_flow DEBUG pause by=key
    LOG core.game_flow INFO screen paused
t=68 enter again       screen=paused menu=play over=retry stepped=False ticks=42 lives=3 waiting=False
t=69 release (paused)  screen=paused menu=play over=retry stepped=False ticks=42 lives=3 waiting=False
    LOG core.game_flow INFO screen playing
t=70 space resume      screen=playing menu=play over=retry stepped=False ticks=42 lives=3 waiting=False
t=71 release           screen=playing menu=play over=retry stepped=True ticks=43 lives=3 waiting=False
== focus_lost: during play, during the pause, on the menu
    LOG core.game_flow DEBUG pause by=focus
    LOG core.game_flow INFO screen paused
t=72 focus lost, play  screen=paused menu=play over=retry stepped=False ticks=43 lives=3 waiting=False
t=73 focus lost, pause screen=paused menu=play over=retry stepped=False ticks=43 lives=3 waiting=False
t=74 paused, none      screen=paused menu=play over=retry stepped=False ticks=43 lives=3 waiting=False
t=75 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=76 focus lost, menu  screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
== pause in a respawn wait, UP pressed in the pause and held after the resume
t=77 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen playing
t=78 enter Play        screen=playing menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=79 release           screen=playing menu=play over=retry stepped=True ticks=1 lives=3 waiting=False
t=142 fall              screen=playing menu=play over=retry stepped=True ticks=64 lives=2 waiting=True
t=143 waiting           screen=playing menu=play over=retry stepped=True ticks=65 lives=2 waiting=True
    LOG core.game_flow DEBUG pause by=key
    LOG core.game_flow INFO screen paused
t=144 enter: pause      screen=paused menu=play over=retry stepped=False ticks=65 lives=2 waiting=True
t=145 UP pressed paused screen=paused menu=play over=retry stepped=False ticks=65 lives=2 waiting=True
t=146 UP held paused    screen=paused menu=play over=retry stepped=False ticks=65 lives=2 waiting=True
    LOG core.game_flow INFO screen playing
t=147 enter: resume     screen=playing menu=play over=retry stepped=False ticks=65 lives=2 waiting=True
t=148 resumed, UP held  screen=playing menu=play over=retry stepped=True ticks=66 lives=2 waiting=True
t=149 UP held           screen=playing menu=play over=retry stepped=True ticks=67 lives=2 waiting=True
t=150 UP released       screen=playing menu=play over=retry stepped=True ticks=68 lives=2 waiting=True
t=151 UP pressed        screen=playing menu=play over=retry stepped=True ticks=69 lives=2 waiting=False
== last life: Enter and focus_lost do nothing; GAME_OVER; choices
t=152 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=1 waiting=False
    LOG core.game_flow INFO screen playing
t=153 enter Play        screen=playing menu=play over=retry stepped=False ticks=0 lives=1 waiting=False
t=154 release           screen=playing menu=play over=retry stepped=True ticks=1 lives=1 waiting=False
    LOG core.run INFO last life score=3
t=217 fall              screen=playing menu=play over=retry stepped=True ticks=64 lives=0 waiting=False
t=218 enter in last lifescreen=playing menu=play over=retry stepped=True ticks=65 lives=0 waiting=False
t=219 release           screen=playing menu=play over=retry stepped=True ticks=66 lives=0 waiting=False
t=220 focus in last lifescreen=playing menu=play over=retry stepped=True ticks=67 lives=0 waiting=False
t=221 none              screen=playing menu=play over=retry stepped=True ticks=68 lives=0 waiting=False
    LOG core.run INFO game over score=3
    LOG core.game_flow INFO screen game_over
t=337 last life         screen=game_over menu=play over=retry stepped=True ticks=184 lives=0 waiting=False
t=338 over, none        screen=game_over menu=play over=retry stepped=False ticks=184 lives=0 waiting=False
    LOG core.game_flow DEBUG game over select menu
t=339 down              screen=game_over menu=play over=menu stepped=False ticks=184 lives=0 waiting=False
t=340 release           screen=game_over menu=play over=menu stepped=False ticks=184 lives=0 waiting=False
    LOG core.game_flow DEBUG game over select retry
t=341 down              screen=game_over menu=play over=retry stepped=False ticks=184 lives=0 waiting=False
t=342 release           screen=game_over menu=play over=retry stepped=False ticks=184 lives=0 waiting=False
    LOG core.game_flow DEBUG game over select menu
t=343 up                screen=game_over menu=play over=menu stepped=False ticks=184 lives=0 waiting=False
t=344 release           screen=game_over menu=play over=menu stepped=False ticks=184 lives=0 waiting=False
    LOG core.game_flow INFO screen menu
t=345 enter MENU        screen=menu menu=play over=menu stepped=False ticks=184 lives=0 waiting=False
t=346 release           screen=menu menu=play over=menu stepped=False ticks=184 lives=0 waiting=False
    LOG core.run INFO new run
    LOG core.game_flow INFO screen playing
t=347 enter Play        screen=playing menu=play over=menu stepped=False ticks=0 lives=3 waiting=False
t=348 release           screen=playing menu=play over=menu stepped=True ticks=1 lives=3 waiting=False
== lose again (3 lives), Enter on RETRY
t=411 playing           screen=playing menu=play over=menu stepped=True ticks=64 lives=2 waiting=True
t=412 playing           screen=playing menu=play over=menu stepped=True ticks=65 lives=2 waiting=False
t=441 playing           screen=playing menu=play over=menu stepped=True ticks=94 lives=2 waiting=False
t=477 playing           screen=playing menu=play over=menu stepped=True ticks=130 lives=1 waiting=True
t=478 playing           screen=playing menu=play over=menu stepped=True ticks=131 lives=1 waiting=False
t=507 playing           screen=playing menu=play over=menu stepped=True ticks=160 lives=1 waiting=False
    LOG core.run INFO last life score=18
t=543 playing           screen=playing menu=play over=menu stepped=True ticks=196 lives=0 waiting=False
    LOG core.run INFO game over score=18
    LOG core.game_flow INFO screen game_over
t=663 playing           screen=game_over menu=play over=retry stepped=True ticks=316 lives=0 waiting=False
    LOG core.run INFO new run
    LOG core.game_flow INFO screen playing
t=664 enter RETRY       screen=playing menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=665 release           screen=playing menu=play over=retry stepped=True ticks=1 lives=3 waiting=False
== add_flow_drifters: paused, page, stepped
t=666 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen playing
t=667 enter Play        screen=playing menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=668 release           screen=playing menu=play over=retry stepped=True ticks=1 lives=3 waiting=False
    LOG core.game_flow DEBUG pause by=key
    LOG core.game_flow INFO screen paused
t=669 enter: pause      screen=paused menu=play over=retry stepped=False ticks=1 lives=3 waiting=False
   paused tick: screen=paused run_stepped=False drifters 0 -> 0 next_uid 1 -> 1
t=670 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow DEBUG menu select instructions
t=671 down              screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
t=672 release           screen=menu menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen instructions
t=673 enter Instructionsscreen=instructions menu=instructions over=retry stepped=False ticks=0 lives=3 waiting=False
   page tick: screen=instructions run_stepped=False drifters 0 -> 0 next_uid 1 -> 1
t=674 release           screen=menu menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
    LOG core.game_flow INFO screen playing
t=675 enter Play        screen=playing menu=play over=retry stepped=False ticks=0 lives=3 waiting=False
t=676 release           screen=playing menu=play over=retry stepped=True ticks=1 lives=3 waiting=False
t=677 play tick         screen=playing menu=play over=retry stepped=True ticks=2 lives=3 waiting=False
   stepped tick: screen=playing run_stepped=True drifters 0 -> 1 next_uid 1 -> 2
```

Reading the output:
- Menu: up from Play wraps to Leaderboard, a second up gives Instructions, down, down gives Play, down gives Instructions (t=2 to t=11). Enter on Instructions opens the page (t=12); Enter held with down on the page does nothing (t=13); a fresh confirm goes back with Play selected (t=15). Enter on Leaderboard opens it (t=21) and a fresh confirm goes back (t=23).
- Enter on Play (t=25) does not step the run; the 40 ticks held step it every tick (t=26 to t=66, no pause). Released (t=67), pressed again: `pause by=key` and `screen paused` (t=68), the run frozen at ticks=42. Resume (t=70) does not step; t=71 does.
- `focus_lost` in play pauses (`pause by=focus`, t=72), does nothing in the pause (t=73) and on the menu (t=76).
- Respawn wait: paused at t=144 with waiting=True. UP pressed at t=145 during the pause and held through the resume (t=147) and t=148 to t=149: still waiting. Released (t=150), pressed (t=151): the wait ends.
- Last life: `last life score=3` at t=217. Enter (t=218) and `focus_lost` (t=220) there: still `playing`, the run steps. `game over score=3` then `screen game_over` at t=337, RETRY selected. Down, down, up: menu, retry, menu (t=339 to t=343). Enter on MENU (t=345): `screen menu`, Play selected, no `new run`. Enter on Play (t=347): `new run`, then `screen playing`, ticks=0, lives=3. Lost again (t=663): Enter on RETRY (t=664): `new run`, `screen playing`, ticks=0.
- `add_flow_drifters`: paused tick, page tick: 0 -> 0 drifters, uid unchanged. Stepped tick: 0 -> 1, next_uid 1 -> 2.
