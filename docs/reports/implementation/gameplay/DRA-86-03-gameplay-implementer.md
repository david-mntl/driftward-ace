Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** build the island block in the ship (`Ground`, `NO_GROUND`, `Ship.against_island`, `spawn_clear`, `block_ship`, the optional `ground` of `step`, the `island contact` log line), task `docs/contracts/DRA-86/tasks/DRA-86-03-gameplay-implementer.md`, from the Architect.
2. **Delivered:** `game/core/ship.py` (changed). Nothing else.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `py_compile game/core/ship.py`: clean.
   - `game/tests/check.sh lint`: ruff check and format pass.
   - Acceptance smoke (the task's command, run from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`), output:
     ```
     284.0 1.1 True
     0.84 False
     216.0 1.1 True
     384.0 0.0 0.16
     0.0526 0.0197 True
     240.4 1.1 True
     224.0 326.0 True
     True
     ```
     All eight lines match the task.
   - Determinism: the same smoke run twice, outputs byte-identical.
   - `check.sh core`: 1572 passed, 5 failed. `check.sh ui`: 45 passed, 1 failed. `check.sh typecheck`: 6 errors, all in `tests/core/test_collision.py`. None touch the ship: the failures are `test_collision.py` (floating_island shape table and variant), `test_wave_files.py` (placement type message lists `floating_island`) and `test_drifter_registry.py` (lists drifter types). They are the ones the drifters contract's DRA-86 Impact table expects until later tasks and the island tuning file exist. Every `test_ship*.py` and `test_run*.py` test passes unchanged. I did not re-run on a clean checkout to prove these fail without my change; they name no ship code.
   - Grep of `game/core/` for the banned names: only false hits (`.wav` matches `.waves` in `core/waves.py` and `run.py`, and ruff.toml's own ban messages). No real use.
4. **Assumptions:** none beyond Decisions.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-86/tasks/DRA-86-03-gameplay-implementer.md`. Left alone: `game/core/run.py` (task DRA-86-04 builds the ground, calls `block_ship` and `spawn_clear`), `collision.py`, the island drifter, tests.
7. **Status:** done.

## Decisions
- Update order is the contract's: steps 1 to 5, walls, then `block_ship`, then the top line. The contract fixes it.
- Log order: `step` logs `wall hit` right after the walls, `block_ship` logs `island contact`, then `step` logs `top line stop`. That gives the contract's order (wall, island, top line). One side effect: `wall hit` now reports the position after the wall clamp, before the island push and the top line (the contract: "the new position after the clamp or the push"). It differs from the old line only on a tick where a wall hit and a top-line stop happen together. No existing test failed on it.
- `block_ship` logs `island contact` when the returned ship has `against_island` True and the input had it False. In `step` the input to `block_ship` carries the previous tick's `against_island`, so riding logs once.
- `_shortest_way_out` loops `push_directions` in order, skips a direction that puts the ship past a side wall (or above the top line when it points up), and replaces the best only when shorter by more than `SURFACE_TOLERANCE`. It raises `RuntimeError` if nothing is allowed, which the contract says can't happen (straight down is never refused). That branch exists for the type checker.
- Speed rule: relative speed against the ground's motion, drop the part into the surface only when `r . n < 0`, add the ground's motion back. Source: ship.md, Rules, Islands, rule 4.
- `spawn_clear` uses `exit_distance` up and down, above when the top edge stays at or below `TOP_LINE_Y` and `up <= down`. Source: ship.md, Respawn spot.
- No number was added. `SURFACE_TOLERANCE` comes from `core.collision`. `_UP` and `_DOWN` are the two unit directions, private `Final` constants.
- `_Push` is a private `NamedTuple` (direction, distance), so the choice reads clearly. The old `_log_contact_starts` was removed: its two lines now sit inline in `step`, to allow the island line between them.
