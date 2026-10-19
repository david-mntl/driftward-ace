Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-76/tasks/DRA-76-05-gameplay-implementer.md` (Architect): the run's waves in `core/run.py`, and `LEVEL_STARTS_M` and `level_at` removed from `core/levels.py`.
2. **Delivered:**
   - `game/core/run.py`: `Run.waves`, `Run.level` (waves' level, else `FIRST_LEVEL`), `Run.wave_spawns_due`, `start_run(waves=None)`, step 3 and step 5 pass `run.level`, new step 9a `_step_run_waves`, the retry through `_next_waves` and `next_run_waves`.
   - `game/core/levels.py`: `LEVEL_STARTS_M` and `level_at` removed; the module docstring no longer mentions where levels start.
3. **Checks:**
   - IS_CE: true. `py_compile` clean on both files.
   - `ruff check .` clean, `ruff format --check .` clean (68 files). `game/tests/check.sh` ends `QA: pass` (env, lint, format, typecheck, core, ui all PASS; existing tests unchanged).
   - Acceptance smoke, run from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<the task's command>"`. Output, matching the task's four lines:
     ```
     1 None ()
     1 w0 ['coin']
     51 2 p 23.21 (1, 0, 0, 0, 0, 0, 0)
     1 w0 True 0
     ```
   - Determinism: ran the same smoke twice, output identical.
   - Grep of `game/core/` for the banned names: no real hit. The matches are `core/ruff.toml` (its ban messages) and `.wav` matching `.waves` / `.wave_id` as a regex; no `.wav` file, no sleep, thread, asyncio, display, event, key or module-level `random`.
4. **Assumptions:** `grep` shows no other user of `level_at` or `LEVEL_STARTS_M` in `game/` (tests included), so removing them breaks nothing; `test_drifters.py` already dropped its use (DRA-76-02).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-76/tasks/DRA-76-05-gameplay-implementer.md`. Left alone: `core/scroll.py`, `core/waves.py`, `core/wave_files.py`, `game/app/`, views, tests, `game/waves/`. The app still has to call `start_run(waves)` and `add_drifters(run, run.wave_spawns_due, ...)` (Integration Engineer).
7. **Status:** done.

## Decisions
- Step 9a runs last, on the result of the drop, with `run.scroll.distance_px` from that result. A game-over tick reaches it too (the freeze applies to the next tick), as the contract says.
- The level is read once going into the tick (`run.level` in step 3 and step 5); step 9a's raised level shows in the returned run only.
- The retry logs `new run` first, then builds the waves with `next_run_waves`, so the new run's `wave start` follows it, as the contract's log order says. A run with no waves calls `start_run()` as before.
- `_step_run_waves` and `_next_waves` are small private helpers so `_step_playing` and `_step_game_over` keep one job each.
- No new numbers: the level multipliers and `FIRST_LEVEL` come from `core/levels.py` (DRA-76-01), the clock from `core/waves.py`.
