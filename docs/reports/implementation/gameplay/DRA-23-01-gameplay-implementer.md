Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-23/tasks/DRA-23-01-gameplay-implementer.md`, from the Architect: build the run (lives, falls, respawn wait, invulnerability and blink, game over, retry) and take the respawn stand-in out of the ship step. Contract: `docs/contracts/systems/run.md`, `docs/contracts/systems/ship.md`.

2. **Delivered:**
   - `game/core/run.py` (new): `LIVES_START`, `INVULN_TICKS`, `BLINK_SWAP_TICKS`, `RESPAWN_WAIT_LIMIT`, `Run` (with `invulnerable`, `ship_visible`), `start_run`, `step_run`, and six `core.run` log lines.
   - `game/core/ship.py` (changed): `step` ends after step 7. The floor check, the `spawn()` return and the `respawn from` line are gone. `_is_below_floor` is now the public `is_below_floor`. Module and `step` docstrings updated. Nothing else touched.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/run.py game/core/ship.py`: clean.
   - `game/tests/check.sh lint`: PASS lint, PASS format (ruff check and ruff format --check, no `noqa`).
   - `game/tests/check.sh core`: 16 passed, 2 failed, exactly the two expected failures in `game/tests/core/test_ship.py`: `test_floor_respawns_at_spawn` and the respawn part of `test_events_log_once`. Both test the DRA-6 respawn stand-in this task removes (`systems/ship.md`, Impact). Task DRA-23-04 replaces them. Not edited.
   - Acceptance smoke, from `game/`:
     ```
     SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "
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
     Output:
     ```
     2 True 320.0 240.0
     False 239.74
     0 True
     3 False 0 240.0
     ```
     Matches the four expected lines.
   - Determinism: the same script run twice gives identical output (diffed, no difference).
   - Log order, DEBUG on, same run: `life lost lives=2`, `respawn from x=320.00 y=500.20 wait=True`, `invulnerable end`, `respawn wait end`, `life lost lives=1`, `respawn from ... wait=True`, `invulnerable end`, `respawn wait end`, `life lost lives=0`, INFO `game over meters=50`, INFO `new run`. No line on idle ticks.
   - Blink after a life-costing fall, states T to T+30: `VVVVVV......VVVVVV......VVVVVVV` (V visible), invuln_ticks_left 0 at the end. Matches the contract table.
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame`, `random.random(`, `.mp3`, `.wav`, `print(`: no hits.

4. **Assumptions:**
   - `invulnerable end` is logged whenever the timer goes from 1 to 0 on a playing tick, including a tick that also falls (the contract's log order puts it before `life lost`). A life-costing fall never coincides with it, since that fall needs the timer at 0 going in.
   - The Director's 2026-10-13 confirmations (held arrow does not end the wait; no respawn on the last life; blink 6 visible, 6 hidden, starting visible; retry press does not thrust) are what the contract already says. Implemented as written.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-23/tasks/DRA-23-01-gameplay-implementer.md`. Left alone: `game/tests/` (two expected failures wait for DRA-23-04), `game/app/`, `game/ui/`, `core/scroll.py`, `core/world.py`. `ship.py` and `run.py` are not yet called from `game/app/` (Integration Engineer).

7. **Status:** done.

## Decisions
- Update order: the contract fixes it. One playing tick is press, timer, wait, ship step (semi-implicit Euler inside `core.ship.step`, unchanged), scroll, fall, `held`. Source: `systems/run.md`, Rules.
- State changes use `dataclasses.replace` on the frozen `Run`, so the input is never mutated. `_step_playing` builds the stepped run, then `_apply_fall` returns the fall result. `step_run` only picks between the playing and game-over paths. Early returns, no nesting.
- `_is_press` zips the four arrow states with `strict=True` (ruff B905). A press is any arrow held now and not on the last tick.
- `_log_respawn(fell_from, *, waits)` takes `waits` only to print it in the log line. It switches no behavior.
- Game over: the ship returned is the stepped ship (where it fell, below the floor), `invuln_ticks_left = 0`, `waiting = False`, `retry_armed = no arrow held`. The retry returns `replace(start_run(), held=thrust)`.
- No number in code beyond the four constants. Sources: `LIVES_START` and `INVULN_TICKS` are locked in 05-lives-and-damage.md. `BLINK_SWAP_TICKS` is the scope report DRA-23 value (0.1 s x 60 ticks/s), not in the GDD (LD-04). `RESPAWN_WAIT_LIMIT = None` per rule 2.5, read by nothing.
- `Run.held` default is `Thrust()`, a frozen instance, so a shared default is safe.
