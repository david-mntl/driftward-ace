Feature: DRA-23
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md#interface
Status: done
Linear: DRA-24

## Do
Build the run: lives, falls, the respawn wait, invulnerability with the blink, game over and retry. Take the respawn stand-in out of the ship step.
- `game/core/ship.py`, from `docs/contracts/systems/ship.md`, Interface, Rules and Impact:
  - `step` ends after step 7 (the top line) and returns that ship. Remove the floor check, the `spawn()` return and the `respawn from` log line from it.
  - Rename `_is_below_floor` to the public `is_below_floor(ship: Ship) -> bool`: True when `ship.y - SHIP_H / 2 >= SCREEN_H`. Pure, no logging.
  - Update the module docstring and `step`'s docstring: no TEMPORARY respawn stand-in any more; the floor check is `is_below_floor`, used by `core.run`. No other change: constants, `Thrust`, `Ship`, `spawn`, steps 1 to 7 and the `wall hit` and `top line stop` lines stay exactly as they are.
- `game/core/run.py` (new), exactly the `core/run.py` block of `docs/contracts/systems/run.md`, Interface, Rules and Logging:
  - Constants, each `Final` with its source in its docstring: `LIVES_START = 3` (05-lives-and-damage.md, locked), `INVULN_TICKS = 30` (05-lives-and-damage.md, locked), `BLINK_SWAP_TICKS = 6` (scope report DRA-23: one visible/hidden swap every 0.1 s, approved in chat, not in the GDD, LD-04; 0.1 s × 60 ticks/s), `RESPAWN_WAIT_LIMIT: Final[int | None] = None` (05-lives-and-damage.md, rule 2.5: no time limit; nothing reads it in DRA-23).
  - `Run`, a frozen, slotted dataclass with the eight fields, defaults and field docs from the contract, and the two properties `invulnerable` and `ship_visible`.
  - `start_run() -> Run`: `Run(ship=spawn(), scroll=start_scroll())`.
  - `step_run(run: Run, thrust: Thrust) -> Run`: the playing tick (steps 1 to 6) and the game-over tick, in the contract's order. Never mutates its input.
  - Logging on the `core.run` logger, exactly the six lines in the contract's Logging section, at the levels given there (four DEBUG, two INFO), in the order given. No other line, never one per tick.
- Imports in `run.py`: stdlib, `core.ship`, `core.scroll`. Never pygame, `ui` or `app`. No frame time, no randomness, no run mode.
- Follow game/CONTEXT.md: module logger, lazy log formatting, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` and `game/tests/check.sh core` before handoff.
- Expected test result: after this change, `check.sh core` fails in exactly two places in `tests/core/test_ship.py`: `test_floor_respawns_at_spawn`, and the respawn part of `test_events_log_once`. Both test the DRA-6 respawn stand-in this task removes (`systems/ship.md`, Impact). Task DRA-23-04 replaces them. Every other core test must pass. Don't edit tests. Name the two failures in the implementation report.

## Acceptance check
From `game/`, run:
```
python -c "
from core.run import start_run, step_run
from core.ship import Thrust
no, up = Thrust(), Thrust(up=True)
r = start_run()
for _ in range(120): r = step_run(r, no)
print(r.lives, r.waiting, r.ship.x, r.ship.y)
r = step_run(r, up); print(r.waiting, round(r.ship.y, 2))
for _ in range(300): r = step_run(r, no)
r = step_run(r, up)
for _ in range(300): r = step_run(r, no)
print(r.lives, r.game_over)
r = step_run(r, up); print(r.lives, r.game_over, r.scroll.meters, r.ship.y)
"
```
It prints four lines:
- `2 True 320.0 240.0`: the first fall cost a life, and the ship waits at the respawn point with no key held.
- `False 239.74`: the Up press ended the wait and thrust on that tick (240 − 0.42 + 0.16).
- `0 True`: the third fall ended the run.
- `3 False 0 240.0`: with every arrow released, one press started a new run.
Put the command and its output in the implementation report.

## Out of scope
- Calling `start_run` and `step_run` in the frame loop, the blink in the draw, the Game Over box call. These are in `game/app/`, built by the Integration Engineer.
- The hearts (task DRA-23-02) and the Game Over box view (task DRA-23-03).
- Tests (tasks DRA-23-04 and DRA-23-05).
- Hazards, hits, the life-lost feedback (flash, breaking heart, burst), score, a time limit on the wait. Out of DRA-23 scope.
- Any change to `core/scroll.py`, `core/world.py`, `game/ui/`, `game/app/` or `game/main.py`.
