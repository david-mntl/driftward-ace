Feature: DRA-6
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/DRA-6/DRA-6-ship.md#interface
Status: done
Linear: DRA-9

## Do
Build the ship's state and its one-tick step, plus the screen geometry it needs.
- `game/core/world.py`: exactly the Interface and Rules of `docs/contracts/DRA-6/DRA-6-world.md`. Constants only: `SCREEN_W`, `SCREEN_H`, `TOP_LINE_RATIO`, `TOP_LINE_Y = round(SCREEN_H * TOP_LINE_RATIO)`. No imports, no logger.
- `game/core/ship.py`: exactly the Interface and Rules of `docs/contracts/DRA-6/DRA-6-ship.md`.
  - The constants, each with its GDD source in its docstring, as the contract lists them.
  - `Thrust` and `Ship` as frozen dataclasses with the fields and defaults given. `x`, `y` are the ship's center.
  - `spawn() -> Ship`: (320, 240), at rest.
  - `step(ship, thrust) -> Ship`: the eight steps in the contract's order. Steps 7 (top-line stop) and 8 (floor respawn) are temporary for DRA-6. Mark them so in their docstrings or comments.
  - Event logging on the `core.ship` logger at DEBUG, with the exact messages in Rules, Logging. Log only when contact starts and on each respawn. Never a line on a tick where nothing happened.
- Imports: stdlib and `core.world` only. Never pygame, `ui` or `app`. No frame time, no randomness, no run mode.
- Follow game/CONTEXT.md: module logger (not in `world.py`, which is constants only), lazy log formatting, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` before handoff.

## Acceptance check
From `game/`, run `python -c "from core.ship import spawn, step, Thrust; s = spawn(); [s := step(s, Thrust(up=True)) for _ in range(300)]; print(s.y, s.vy)"`. It prints `184.0 0.0`: the ship climbed with Up held and its top edge stopped on the top line at y 168. Put the command and output in the implementation report.

## Out of scope
- The frame loop, reading keys, building `Thrust` from pygame, logging key presses, F3. These are in `game/app/`, built by the Integration Engineer.
- Drawing the ship or the overlay (tasks DRA-6-02 and the overlay task).
- Tests (task DRA-6-03).
- A tuning file, camera, lives, invulnerability, feedback, hazards. Out of DRA-6 scope.
- Any change to `game/app/`, `game/ui/` or `game/main.py`.
