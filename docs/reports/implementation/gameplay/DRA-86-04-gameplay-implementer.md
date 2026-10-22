Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-86/tasks/DRA-86-04-gameplay-implementer.md`: the islands in `core.run` (`island_ground`, steps 4 and 6, the `respawn clear of island` line), from the Architect.
2. **Delivered:** `game/core/run.py` (changed).
3. **Checks:**
   - IS_CE true (pygame-ce 2.5.8). `py_compile game/core/run.py` clean.
   - `ruff check .` and `ruff format --check .` clean; `tests/check.sh lint` PASS.
   - Smoke, from `game/`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <the task's acceptance script>` (the script is the task's `python -c` body, run from a scratch file, not saved in the repo). Output:
     ```
     254.0 True 3
     326.0 True 2
     241.2 True 1.1
     1 1.1 True
     ```
     This matches the four expected lines.
   - Determinism: ran it twice, outputs identical.
   - Grep of `game/core/` for the forbidden calls: only false hits (`.wav` inside `core.waves` / `self.waves`, and the ban messages in `core/ruff.toml`). Nothing to remove.
   - `tests/check.sh typecheck`: 6 errors, all in `tests/core/test_collision.py:589,596` (Polygon union attrs), from the collision change, not `run.py`. `tests/check.sh core`: 1572 passed, 5 failed: `test_collision.py` (2: shape table, floating_island variant) and `test_wave_files.py` (3: the drifter-type list now names `floating_island`). All are outside `run.py` and are the old tests the DRA-86 Impact table expects until the QA tasks. No run test fails; the existing run tests pass unchanged. I did not run `ui`.
4. **Assumptions:** The failures above are the expected ones from the Impact table. I did not check each against the drifters contract's table line by line.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-86/tasks/DRA-86-04-gameplay-implementer.md`. Left alone: `ship.py`, `collision.py`, the island, tests (out of scope).
7. **Status:** done.

## Decisions
- `island_ground(drifters, scroll_step_px)`: one generator over ACTIVE drifters with `effect_on_touch()` BLOCK, their `current_hitbox()` shapes in drifter order, joined. Returns `NO_GROUND` when empty, so a run with no island passes the same object as before. Velocity x is 0.0, velocity y is the scroll step. Source: run.md, Interface.
- Step 4: the scroll step is now computed once in `_step_playing` (`scroll_step_px(run.scroll, run.level)`) and passed to `_update_drifters` and `island_ground`, so step 3 and the ground use the same number. The ground is built from the drifters after step 3. A waiting ship goes through `block_ship`, otherwise `step(ship, thrust, ground)`. Islands block whatever the invulnerability, as the contract says.
- Step 6: `_apply_fall` takes the ground and respawns with `spawn_clear(ground)` in the protected and the unprotected branches. The last-life branch keeps the ship where it fell.
- Log: `respawn clear of island y=%.2f` is emitted from `_respawn_ship` only when the new y differs from `spawn().y`. It is called after `_log_respawn`, so it follows `respawn from`, as the contract's order says.
- No number added; nothing new in tuning. Steps 5a, 7, 8, 9 untouched.

## Review fix 2026-10-21: docs/reports/review/DRA-86-04-gameplay-implementer.md

Fixed: DRA-86-04-F1

1. **Task:** answer review finding DRA-86-04-F1 (should-fix, round 1): run `ui` and report it, from the Implementation Reviewer.
2. **Delivered:** no code change. This section only (`docs/reports/implementation/gameplay/DRA-86-04-gameplay-implementer.md`).
3. **Checks:**
   - `tests/check.sh ui` (from `game/`): 45 passed, 1 failed. The one failure is `tests/ui/test_drifter_registry.py::test_drifter_lists_match_everywhere`: the tuning files list has no `floating_island` while `DrifterType` has it. The DRA-86 Impact table expects it (`docs/contracts/systems/drifters.md:1708`: fails from task DRA-86-02 until `floating_island_view.py` (DRA-86-06) and `game/tuning/drifters/floating_island.json` exist). `test_hud.py` and `test_game_over.py`, which build runs, pass.
   - Rerun: IS_CE true; `py_compile game/core/run.py` clean; `ruff check .` and `ruff format --check .` clean.
   - Smoke rerun (the task's acceptance script, from `game/`, with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <script>`): `254.0 True 3`, `326.0 True 2`, `241.2 True 1.1`, `1 1.1 True`. Two runs, identical output.
   - Grep of `game/core/`: unchanged from the first report, no new hits.
4. **Assumptions:** none new.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-86-04-gameplay-implementer.md`.
7. **Status:** done.

## Decisions (review fix)
- No code touched: F1 asked for a check result in the report, not a code change.
- F2 asks for no change (the parameter name is the contract's Interface), so it is not answered as a fix.

## Answers
- DRA-86-04-F1. Fixed: this section, Checks: `ui` run, 1 failure named (`test_drifter_registry.py`), matched to the Impact row at `docs/contracts/systems/drifters.md:1708`.
