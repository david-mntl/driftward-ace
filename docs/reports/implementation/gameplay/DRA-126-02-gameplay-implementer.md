Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-126-02 (Architect): the saves in `game/core/game_flow.py`, from `docs/contracts/systems/game-flow.md` (DRA-126 parts).
2. **Delivered:**
   - `game/core/game_flow.py` (changed): `GameFlow` gains `saves`, `game_over_message`, `picker`, `picking`, `saves_changed` (all with defaults) and the properties `best` and `leaderboard`; `start_flow(run, saves=None)`; new `stop_saves`; opening GAME_OVER by the run's place; the picker's keys and the name save; the three new log lines and the picker log lines.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `py_compile` on `core/game_flow.py`: clean.
   - `game/tests/check.sh lint`: PASS lint, PASS format. `check.sh typecheck`: PASS (mypy --strict, 116 files). `check.sh ui`: 89 passed.
   - `check.sh core`: 3287 passed, 1 failed: `test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`, the one failure `impact.md` expects from this task (the flow now logs `game over message=game_over place=none` before `screen game_over`; cleared by DRA-126-07). No other test changed or fails.
   - Smoke script below, from `/workspace/game`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python <script>`, run twice; the two outputs are byte-identical (`cmp`). It shows each acceptance bullet: section 1 (blank picker, up/down/down/left/right as fresh presses, one up held 30 ticks stepped once, ACE, Enter held 30 ticks: `changed=1` on the first held tick only and no RETRY; release, Enter: new run, `best=0`, the saved score); section 2 (picker starts with `ACE`; TOP_3 at place 2, TOP_10 at place 4); section 3 (full list: GAME_OVER, no picker, up and down move RETRY and MENU, up with down together does not); section 4 (no saves: GAME_OVER, no picker, `best` None, `leaderboard` empty); section 5 (all slots blank: `saves is before` True, `last_nickname` None, `changed=0`); section 6 (`stop_saves` the tick after the save: `best` None, screen still `game_over`, the next game over has no picker).
   - Grep of `core/game_flow.py` for the banned names: no hit.
4. **Assumptions:**
   - Run scores in the smoke are 0 (a falling ship dies at once), so the saved entry is `score=0 level=1` and a run ties an entry of score 0 and goes under it (place 2 in section 2). Higher scores in sections 2b and 3 come from seeded `Saves`.
   - Section 2 and the last block of section 6 swap in a new dying run after RETRY (`replace(flow, run=dying_run())`) because the run `next_run` builds takes much longer to die. A test device only; no code does it.
   - A confirm on a picker whose `saves` is None (only possible if `stop_saves` came while picking) ends the picking and saves nothing, with no log line. The contract names no such case; core must not raise on it.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-126/tasks/DRA-126-02-gameplay-implementer.md`. DRA-126-07 must update the one test named above. Left alone: `core/saves.py`, `core/run.py`, ui, tests, app.
7. **Status:** done.

## Decisions
- Presses: `_Presses` gains `left` and `right`, read like up and down against `arrows_held`. Source: game-flow.md, Rules, Presses.
- `saves_changed` is cleared with `run_stepped` at the start of every tick (`replace(flow, run_stepped=False, saves_changed=False)`), and set only by `_confirm_name` with a name. An empty-name confirm leaves it False.
- Opening GAME_OVER is its own function, `_open_game_over`: it sets the selection, message, picker and picking together, so nothing from an earlier game over survives. The message is logged at DEBUG right before `_enter` logs `screen game_over`.
- The picker turns the character first, then moves the cursor, so the slot logged and turned is the one the cursor was on going in. Up and down together, or left and right together, cancel (`up != down`). A confirm press ignores the arrows on its tick.
- `_confirm_name` computes the place again with `place_of` for the log line only; the saves cannot have changed since the screen opened, so it is the opening place. `add_entry` raises if it were not, which would be a bug.
- `picking` True with `picker` None cannot happen by construction; `_step_game_over` treats it as not picking so the type narrows without an assert.
- Update order, wall handling: not in this task. No tuning keys, no numbers: the places, the characters and the steps come from `core.saves`.
- `best` and `leaderboard` read `saves` only, so BEST changes only on a save tick.

## Smoke script
Saved in the scratchpad while checking, not in the repo.

```python
"""DRA-126-02 smoke. Run from game/: python <this file>."""

import logging
import sys
from dataclasses import replace

sys.path.insert(0, ".")

from core.game_flow import (
    GameFlow,
    Screen,
    TickInput,
    start_flow,
    step_flow,
    stop_saves,
)
from core.last_life import LastLifeRules
from core.run import Run, start_run
from core.saves import Saves, ScoreEntry
from core.ship import Ship, Thrust

DELAY = 3
FLOOR_Y = 480 + 32 / 2 - 5.5
IDLE = TickInput()
ENTER = TickInput(confirm=True)
UP = TickInput(thrust=Thrust(up=True))
DOWN = TickInput(thrust=Thrust(down=True))
LEFT = TickInput(thrust=Thrust(left=True))
RIGHT = TickInput(thrust=Thrust(right=True))


class Printer(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        print(f"        log {record.name} {record.levelname}: {record.getMessage()}")


root = logging.getLogger("core")
root.setLevel(logging.DEBUG)
root.addHandler(Printer())


def dying_run() -> Run:
    """A one-life run whose ship falls past the floor next step."""
    rules = LastLifeRules(delay_ticks=DELAY)
    ship = Ship(x=200.0, y=FLOOR_Y, vx=0.0, vy=5.5)
    return replace(start_run(last_life_rules=rules), ship=ship, lives=1)


def picker_text(flow: GameFlow) -> str:
    if flow.picker is None:
        return "-"
    return "".join(c if c != " " else "." for c in flow.picker.slots) + f"@{flow.picker.cursor}"


tick = 0


def go(flow: GameFlow, keys: TickInput, note: str = "") -> GameFlow:
    global tick
    tick += 1
    out = step_flow(flow, keys)
    print(
        f"  t{tick:03d} {note:<24} {out.screen.value:<9} msg={out.game_over_message.value:<14} "
        f"picking={int(out.picking)} picker={picker_text(out):<13} sel={out.game_over_selection.value:<5} "
        f"changed={int(out.saves_changed)} best={out.best} board={len(out.leaderboard)}"
    )
    return out


def hold(flow: GameFlow, keys: TickInput, ticks: int, note: str) -> GameFlow:
    for i in range(ticks):
        flow = go(flow, keys, f"{note} (tick {i + 1}/{ticks})" if i in (0, ticks - 1) else "")
    return flow


def tap(flow: GameFlow, keys: TickInput, note: str) -> GameFlow:
    flow = go(flow, keys, note)
    return go(flow, IDLE, "release")


def to_game_over(flow: GameFlow) -> GameFlow:
    """Release everything, press Play, then idle until GAME_OVER."""
    flow = go(flow, IDLE, "release")
    flow = go(flow, ENTER, "Play")
    while flow.screen is Screen.PLAYING:
        flow = go(flow, IDLE, "idle")
    flow = go(flow, IDLE, "release")
    return flow


def retry_with_dying_run(flow: GameFlow) -> GameFlow:
    """Press RETRY, then swap in a dying run (a test device, the real run lasts longer)."""
    flow = go(flow, ENTER, "RETRY")
    flow = replace(flow, run=dying_run())
    while flow.screen is Screen.PLAYING:
        flow = go(flow, IDLE, "idle")
    return go(flow, IDLE, "release")


def entry(score: int) -> ScoreEntry:
    return ScoreEntry(nickname="TOP", score=score, level_reached=1)


print("== 1. start_flow(run, Saves()): NEW_BEST_SCORE, blank picker, ACE, save, new run")
flow = start_flow(dying_run(), Saves())
flow = to_game_over(flow)
print("  run score:", flow.run.score, "level_reached:", flow.run.level_reached)
flow = tap(flow, UP, "up")
flow = tap(flow, DOWN, "down")
flow = tap(flow, DOWN, "down")
flow = tap(flow, LEFT, "left")
flow = tap(flow, RIGHT, "right")
flow = tap(flow, UP, "up, one held 30 ticks follows")
flow = hold(flow, UP, 30, "up held")
flow = go(flow, IDLE, "release")
# slot 0 now: up from blank twice more is needed for A; walk by reading the picker
print("  picker now", picker_text(flow))
while flow.picker.slots[0] != "A":
    flow = tap(flow, UP, "up to A")
flow = tap(flow, RIGHT, "right")
while flow.picker.slots[1] != "C":
    flow = tap(flow, UP, "up to C")
flow = tap(flow, RIGHT, "right")
while flow.picker.slots[2] != "E":
    flow = tap(flow, UP, "up to E")
saves_changed_ticks = []
for i in range(30):
    flow = go(flow, ENTER, "Enter held" if i in (0, 29) else "")
    if flow.saves_changed:
        saves_changed_ticks.append(i + 1)
print("  saves_changed on held ticks:", saves_changed_ticks, "screen:", flow.screen.value)
print("  saves:", flow.saves)
flow = go(flow, IDLE, "release")
flow = go(flow, ENTER, "Enter: RETRY")
print("  new run: screen", flow.screen.value, "best", flow.best)

print("== 2. the next game over with the same saves: picker starts with ACE")
saved = flow.saves
flow = replace(flow, run=dying_run())
while flow.screen is Screen.PLAYING:
    flow = go(flow, IDLE, "idle")
print("  picker:", picker_text(flow), "message:", flow.game_over_message.value)

print("== 2b. place 2 (TOP_3) and place 4 (TOP_10)")
base = dying_run()
top = base.score + 100
for label, scores in (("place 2", [top]), ("place 4", [top, top, top])):
    s = Saves(entries=tuple(entry(x) for x in scores))
    f = to_game_over(start_flow(dying_run(), s))
    print(f"  {label}: message={f.game_over_message.value} picker={picker_text(f)}")

print("== 3. a full list no run beats: GAME_OVER, no picker, up and down move the choice")
full = Saves(entries=tuple(entry(10_000) for _ in range(10)))
flow = to_game_over(start_flow(dying_run(), full))
flow = tap(flow, UP, "up")
flow = tap(flow, DOWN, "down")
flow = go(flow, TickInput(thrust=Thrust(up=True, down=True)), "up and down together")

print("== 4. start_flow(run), no saves")
flow = start_flow(dying_run())
print("  at start: best", flow.best, "leaderboard", flow.leaderboard)
flow = to_game_over(flow)
print("  best", flow.best, "leaderboard", flow.leaderboard, "picker", flow.picker)

print("== 5. a picker confirmed with every slot blank")
before = Saves()
flow = to_game_over(start_flow(dying_run(), before))
flow = go(flow, ENTER, "Enter, all blank")
print("  saves is before:", flow.saves is before, "last_nickname:", flow.saves.last_nickname,
      "entries:", len(flow.saves.entries))

print("== 6. stop_saves on the tick after a save")
flow = to_game_over(start_flow(dying_run(), Saves()))
flow = tap(flow, UP, "up")
flow = go(flow, ENTER, "Enter: save A")
flow = go(flow, IDLE, "the tick after the save")
flow = stop_saves(flow)
print("  after stop_saves: screen", flow.screen.value, "best", flow.best, "board",
      len(flow.leaderboard), "picking", flow.picking, "saves_changed", flow.saves_changed)
flow = go(flow, IDLE, "idle")
flow = retry_with_dying_run(flow)
print("  next game over: picker", picker_text(flow), "message", flow.game_over_message.value)
```

## Smoke output
`changed` is `saves_changed`, `board` the number of `leaderboard` entries, `picker` the slots (`.` is a blank) and `@` the cursor. Log lines print above the row of the tick that wrote them.

```
== 1. start_flow(run, Saves()): NEW_BEST_SCORE, blank picker, ACE, save, new run
  t001 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.game_flow INFO: screen playing
  t002 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t003 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t004 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t005 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=new_best_score place=1
        log core.game_flow INFO: screen game_over
  t006 idle                     game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
  t007 release                  game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
  run score: 0 level_reached: 1
        log core.game_flow DEBUG: picker slot=0 char='A'
  t008 up                       game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t009 release                  game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=0 char=' '
  t010 down                     game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
  t011 release                  game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=0 char='*'
  t012 down                     game_over msg=new_best_score picking=1 picker=*.........@0  sel=retry changed=0 best=None board=0
  t013 release                  game_over msg=new_best_score picking=1 picker=*.........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker cursor=9
  t014 left                     game_over msg=new_best_score picking=1 picker=*.........@9  sel=retry changed=0 best=None board=0
  t015 release                  game_over msg=new_best_score picking=1 picker=*.........@9  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker cursor=0
  t016 right                    game_over msg=new_best_score picking=1 picker=*.........@0  sel=retry changed=0 best=None board=0
  t017 release                  game_over msg=new_best_score picking=1 picker=*.........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=0 char=' '
  t018 up, one held 30 ticks follows game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
  t019 release                  game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=0 char='A'
  t020 up held (tick 1/30)      game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t021                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t022                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t023                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t024                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t025                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t026                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t027                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t028                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t029                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t030                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t031                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t032                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t033                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t034                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t035                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t036                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t037                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t038                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t039                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t040                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t041                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t042                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t043                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t044                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t045                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t046                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t047                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t048                          game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t049 up held (tick 30/30)     game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t050 release                  game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  picker now A.........@0
        log core.game_flow DEBUG: picker cursor=1
  t051 right                    game_over msg=new_best_score picking=1 picker=A.........@1  sel=retry changed=0 best=None board=0
  t052 release                  game_over msg=new_best_score picking=1 picker=A.........@1  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=1 char='A'
  t053 up to C                  game_over msg=new_best_score picking=1 picker=AA........@1  sel=retry changed=0 best=None board=0
  t054 release                  game_over msg=new_best_score picking=1 picker=AA........@1  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=1 char='B'
  t055 up to C                  game_over msg=new_best_score picking=1 picker=AB........@1  sel=retry changed=0 best=None board=0
  t056 release                  game_over msg=new_best_score picking=1 picker=AB........@1  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=1 char='C'
  t057 up to C                  game_over msg=new_best_score picking=1 picker=AC........@1  sel=retry changed=0 best=None board=0
  t058 release                  game_over msg=new_best_score picking=1 picker=AC........@1  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker cursor=2
  t059 right                    game_over msg=new_best_score picking=1 picker=AC........@2  sel=retry changed=0 best=None board=0
  t060 release                  game_over msg=new_best_score picking=1 picker=AC........@2  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=2 char='A'
  t061 up to E                  game_over msg=new_best_score picking=1 picker=ACA.......@2  sel=retry changed=0 best=None board=0
  t062 release                  game_over msg=new_best_score picking=1 picker=ACA.......@2  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=2 char='B'
  t063 up to E                  game_over msg=new_best_score picking=1 picker=ACB.......@2  sel=retry changed=0 best=None board=0
  t064 release                  game_over msg=new_best_score picking=1 picker=ACB.......@2  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=2 char='C'
  t065 up to E                  game_over msg=new_best_score picking=1 picker=ACC.......@2  sel=retry changed=0 best=None board=0
  t066 release                  game_over msg=new_best_score picking=1 picker=ACC.......@2  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=2 char='D'
  t067 up to E                  game_over msg=new_best_score picking=1 picker=ACD.......@2  sel=retry changed=0 best=None board=0
  t068 release                  game_over msg=new_best_score picking=1 picker=ACD.......@2  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=2 char='E'
  t069 up to E                  game_over msg=new_best_score picking=1 picker=ACE.......@2  sel=retry changed=0 best=None board=0
  t070 release                  game_over msg=new_best_score picking=1 picker=ACE.......@2  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: name saved nickname='ACE' place=1 score=0 level=1
  t071 Enter held               game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=1 best=0 board=1
  t072                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t073                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t074                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t075                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t076                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t077                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t078                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t079                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t080                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t081                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t082                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t083                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t084                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t085                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t086                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t087                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t088                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t089                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t090                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t091                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t092                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t093                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t094                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t095                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t096                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t097                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t098                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t099                          game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t100 Enter held               game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  saves_changed on held ticks: [1] screen: game_over
  saves: Saves(entries=(ScoreEntry(nickname='ACE', score=0, level_reached=1),), last_nickname='ACE')
  t101 release                  game_over msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
        log core.run INFO: new run
        log core.game_flow INFO: screen playing
  t102 Enter: RETRY             playing   msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  new run: screen playing best 0
== 2. the next game over with the same saves: picker starts with ACE
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t103 idle                     playing   msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t104 idle                     playing   msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
  t105 idle                     playing   msg=new_best_score picking=0 picker=ACE.......@2  sel=retry changed=0 best=0 board=1
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=top_3 place=2
        log core.game_flow INFO: screen game_over
  t106 idle                     game_over msg=top_3          picking=1 picker=ACE.......@0  sel=retry changed=0 best=0 board=1
  picker: ACE.......@0 message: top_3
== 2b. place 2 (TOP_3) and place 4 (TOP_10)
  t107 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=1
        log core.game_flow INFO: screen playing
  t108 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=1
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t109 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=1
  t110 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=1
  t111 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=1
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=top_3 place=2
        log core.game_flow INFO: screen game_over
  t112 idle                     game_over msg=top_3          picking=1 picker=..........@0  sel=retry changed=0 best=100 board=1
  t113 release                  game_over msg=top_3          picking=1 picker=..........@0  sel=retry changed=0 best=100 board=1
  place 2: message=top_3 picker=..........@0
  t114 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=3
        log core.game_flow INFO: screen playing
  t115 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=3
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t116 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=3
  t117 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=3
  t118 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=100 board=3
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=top_10 place=4
        log core.game_flow INFO: screen game_over
  t119 idle                     game_over msg=top_10         picking=1 picker=..........@0  sel=retry changed=0 best=100 board=3
  t120 release                  game_over msg=top_10         picking=1 picker=..........@0  sel=retry changed=0 best=100 board=3
  place 4: message=top_10 picker=..........@0
== 3. a full list no run beats: GAME_OVER, no picker, up and down move the choice
  t121 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
        log core.game_flow INFO: screen playing
  t122 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t123 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
  t124 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
  t125 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=game_over place=none
        log core.game_flow INFO: screen game_over
  t126 idle                     game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
  t127 release                  game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
        log core.game_flow DEBUG: game over select menu
  t128 up                       game_over msg=game_over      picking=0 picker=-             sel=menu  changed=0 best=10000 board=10
  t129 release                  game_over msg=game_over      picking=0 picker=-             sel=menu  changed=0 best=10000 board=10
        log core.game_flow DEBUG: game over select retry
  t130 down                     game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
  t131 release                  game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
  t132 up and down together     game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=10000 board=10
== 4. start_flow(run), no saves
  at start: best None leaderboard ()
  t133 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.game_flow INFO: screen playing
  t134 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t135 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t136 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t137 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=game_over place=none
        log core.game_flow INFO: screen game_over
  t138 idle                     game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t139 release                  game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  best None leaderboard () picker None
== 5. a picker confirmed with every slot blank
  t140 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.game_flow INFO: screen playing
  t141 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t142 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t143 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t144 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=new_best_score place=1
        log core.game_flow INFO: screen game_over
  t145 idle                     game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
  t146 release                  game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: name empty, nothing saved
  t147 Enter, all blank         game_over msg=new_best_score picking=0 picker=..........@0  sel=retry changed=0 best=None board=0
  saves is before: True last_nickname: None entries: 0
== 6. stop_saves on the tick after a save
  t148 release                  menu      msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.game_flow INFO: screen playing
  t149 Play                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t150 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t151 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t152 idle                     playing   msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=new_best_score place=1
        log core.game_flow INFO: screen game_over
  t153 idle                     game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
  t154 release                  game_over msg=new_best_score picking=1 picker=..........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: picker slot=0 char='A'
  t155 up                       game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
  t156 release                  game_over msg=new_best_score picking=1 picker=A.........@0  sel=retry changed=0 best=None board=0
        log core.game_flow DEBUG: name saved nickname='A' place=1 score=0 level=1
  t157 Enter: save A            game_over msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=1 best=0 board=1
  t158 the tick after the save  game_over msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=0 best=0 board=1
  after stop_saves: screen game_over best None board 0 picking False saves_changed False
  t159 idle                     game_over msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=0 best=None board=0
        log core.run INFO: new run
        log core.game_flow INFO: screen playing
  t160 RETRY                    playing   msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=0 best=None board=0
        log core.run DEBUG: life lost lives=0
        log core.run INFO: last life score=0
  t161 idle                     playing   msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=0 best=None board=0
  t162 idle                     playing   msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=0 best=None board=0
  t163 idle                     playing   msg=new_best_score picking=0 picker=A.........@0  sel=retry changed=0 best=None board=0
        log core.run INFO: game over score=0
        log core.game_flow DEBUG: game over message=game_over place=none
        log core.game_flow INFO: screen game_over
  t164 idle                     game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  t165 release                  game_over msg=game_over      picking=0 picker=-             sel=retry changed=0 best=None board=0
  next game over: picker - message game_over
```
