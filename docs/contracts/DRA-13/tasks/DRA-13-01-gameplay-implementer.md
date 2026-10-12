Feature: DRA-13
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/DRA-13/DRA-13-scroll.md#interface
Status: done
Linear: DRA-14

## Do
Build the world scroll and the distance counter, and update two stale docstrings.
- `game/core/scroll.py`: exactly the Interface and Rules of `docs/contracts/DRA-13/DRA-13-scroll.md` (the `core/scroll.py` block).
  - The constants, each with its GDD source in its docstring: `SCROLL_BASE = 1.1` (guess), `LEVEL_1_SCROLL_MULT = 1.0` (locked), `SCROLL_PER_TICK = SCROLL_BASE * LEVEL_1_SCROLL_MULT`, `SCROLL_START_DELAY = 30` (guess), `DISTANCE_START = 0` (locked), `PX_PER_METER = 10` (locked).
  - `Scroll` as a frozen dataclass with `ticks: int = 0` and `scrolled_ticks: int = 0`, and two properties: `distance_px` (`DISTANCE_START * PX_PER_METER + scrolled_ticks * SCROLL_PER_TICK`) and `meters` (`math.floor(distance_px / PX_PER_METER)`).
  - `start_scroll() -> Scroll`: ticks 0, scrolled_ticks 0.
  - `step_scroll(scroll: Scroll) -> Scroll`: `ticks + 1`. If the new `ticks` is greater than `SCROLL_START_DELAY`, `scrolled_ticks + 1`. Never mutates its input.
  - Logging on the `core.scroll` logger at DEBUG: `scroll start tick=%d`, once, on the tick the returned scroll has `scrolled_ticks == 1`. No other line.
- `game/core/ship.py`: docstrings only. The module docstring and `_stop_at_top_line` call the top-line stop TEMPORARY and tie it to a camera. Reword them: the top line is a ceiling (03-world-and-camera.md, rule 2; 04-ship.md, rule 2, step 7). Keep the floor respawn marked TEMPORARY. No code change. See `docs/contracts/DRA-6/DRA-6-ship.md`, Impact.
- `game/core/world.py`: module docstring only. Replace "DRA-6 has no camera, so world and screen are the same space." with: the screen is fixed and never moves, there is no camera, and the rules use screen px. No constant changes. See `docs/contracts/DRA-6/DRA-6-world.md`, Impact.
- Imports in `scroll.py`: stdlib only. Never pygame, `ui`, `app`, or `core.ship`. No frame time, no randomness, no run mode.
- Follow game/CONTEXT.md: module logger, lazy log formatting, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` and `game/tests/check.sh core` before handoff. The existing ship tests must still pass.

## Acceptance check
From `game/`, run:
`python -c "from core.scroll import start_scroll, step_scroll; s = start_scroll(); [s := step_scroll(s) for _ in range(30)]; print(s.distance_px, s.meters); [s := step_scroll(s) for _ in range(100)]; print(round(s.distance_px, 2), s.meters)"`
It prints `0.0 0`, then `110.0 11`: the world stays still for the first 30 ticks, then 100 ticks at 1.1 px give 110 px, which is 11 whole meters. Put the command and output in the implementation report.

## Out of scope
- Creating and stepping the scroll in the frame loop, and the draw order. These are in `game/app/`, built by the Integration Engineer.
- The starfield (task DRA-13-02) and the HUD (task DRA-13-03).
- Tests (task DRA-13-04).
- Levels, level speed changes, score, coins, lives, hazards. Out of DRA-13 scope.
- Any change to ship behavior, constants or log lines. Any change to `game/app/`, `game/ui/` or `game/main.py`.
