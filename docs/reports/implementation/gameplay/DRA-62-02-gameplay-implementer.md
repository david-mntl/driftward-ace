Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Add `scroll_step_px` to the scroll, and the scroll step, popups (3a) and collect (5a) to the run, from `docs/contracts/DRA-62/tasks/DRA-62-02-gameplay-implementer.md` (Architect).

2. **Delivered:**
   - `game/core/scroll.py`: `scroll_step_px(scroll) -> float`.
   - `game/core/run.py`: `Run.popups` field; step 3 builds `TickContext(ship, scroll_step_px(run.scroll))`; step 3a (`step_popups`); step 5a in the new `_collects` and `_apply_collect`; `start_run` and `coin_points` docstrings.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/run.py game/core/scroll.py`: clean.
   - `ruff check game` and `ruff format --check game`: clean. `game/tests/check.sh lint` PASS, `check.sh typecheck` PASS (mypy strict, 60 files).
   - `check.sh core`: 1342 passed, 1 failed: `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[coin-None]` ("no tuning file for 'coin'"), the case the contract's DRA-62 Impact table expects until `game/tuning/drifters/coin.json` and DRA-62-05 exist. Every other test passes unchanged.
   - Acceptance command (the task's, verbatim, from `game/`; saved outside the repo and run as `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <script>`). Output:
     ```
     0.0 1.1
     0 1 0
     50 50 0 240.0
     1 210.5
     0
     ```
     All five lines match the acceptance check.
   - Determinism: ran it twice, `diff` empty.
   - Grep of `game/core/` (`*.py`) for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no hits.

4. **Assumptions:** None beyond the Decisions below.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-62/tasks/DRA-62-02-gameplay-implementer.md`. Left alone: `game/core/drifters/`, `game/core/popup.py`, `game/tuning/`, `game/app/`, `game/ui/`, tests, steps 1, 2, 4, 6, 7, 8, 10, `add_drifters` and `step_scroll`.

7. **Status:** done.

## Decisions
- `scroll_step_px` tests `scroll.ticks + 1 > SCROLL_START_DELAY`, the same comparison `step_scroll` uses. Value `SCROLL_PER_TICK`; no new number. Source: systems/scroll.md, The next step's movement.
- Step 5a runs only when the ship was stepped in step 4 (`not stands`, the existing local for "waiting after step 4"). A press that ends the wait steps the ship, so it collects on that tick. Source: systems/run.md, step 5a and Rationale.
- Step 5a tests `ship_hitbox` of the ship from step 4, before the fall check, so a ship that falls on the tick still collects. Fall and hit then read the run returned by `_apply_collect`; their code is unchanged. The cool-down still gets the drifters as they went into step 7 (after collect). A collected drifter is GONE, so `_touches_ship` (which needs ACTIVE) never sees it, and step 9 drops it with its `drifter gone` line.
- `_apply_collect` follows the shape of `_apply_hit`: compute the flags, return the run unchanged when none is set, else build the new tuples. The `drifter touch ... effect=collect` lines log after `invulnerable end` and before the fall or hit lines, as the contract's order says. It logs `effect_on_touch().value`, the same expression the hit uses.
- The run never names the coin: it uses `effect_on_touch()`, `collect_points()` and `collect_popup()` from the base. A popup that is None is not added.
- Popups age in step 3a with the drifters' update, before the collect, so a new popup starts at age 0 on its own tick. Game-over ticks skip `_step_playing`, so popups freeze with the rest and a retry's `start_run()` starts with none.
