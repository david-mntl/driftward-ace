Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-111-03 (`docs/contracts/DRA-111/tasks/DRA-111-03-qa-engineer.md`): the electric ball's tests in `game/tests/core/test_electric_ball.py`, started by `/implement`.
2. **Delivered:**
   - `game/tests/core/test_electric_ball.py` (new): 17 test functions, 18 cases (the cycle test runs at Level 1 and Level 8). One test per `## Test` line, in the task's order: born and start; refusals; fall and WARNING; the cycle; rays and outline; ball on screen; off screen; hitbox and graze zone; drawn parts; the top timeline in the run; level scaling; `telegraph_ticks`; `electric_ball_hitbox` and `check_electric_ball_variant`; the hit, the cooldown and invulnerability in the run (two tests); logs; no mutation and same result (`determinism`).
   - `game/tests/CONTEXT.md`: a paragraph for the new file, placed before `test_floating_island.py`.
   - `docs/reports/qa/DRA-111-03-qa-engineer.md` (this file).
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck PASS (lint and format pass with the new file, mypy `--strict` clean). ui PASS (46). `core` FAIL, and only on `impact.md`'s expected rows: the `test_collision.py` collection error (`KeyError: 'hitbox'` reading `electric_ball.json`, cleared by DRA-111-04) and 5 cases in `test_wave_files.py` that spell out the type list ending `planet, ufo` (cleared by DRA-111-05). With `test_collision.py` left out, `pytest core` gives 819 passed, 5 failed, the same 5. `test_electric_ball.py` is in the `core` step and all 18 of its cases pass (`pytest core/test_electric_ball.py`: 18 passed). Last line `QA: fail (core)`, the state `impact.md` expects until DRA-111-04 and DRA-111-05 land. The acceptance check reads `QA: pass` once those are cleared.
   - Every new test passes against `game/core/drifters/electric_ball.py`: no bug found.
   - Sensitivity check, in a scratchpad copy of `game/` (never in the repo): 7 one-line mutations of `electric_ball.py` each fail between 2 and 7 of the new tests: firing from `>` instead of `>=` (7), rays without the `1 +` (3), `ball_on_screen` with `>= 0` (6), the hitbox gated on `is_firing` instead of `pulse_fires` (2), the scroll added to the fall (5), the Timer × dropped from the charge (4), the outline level made all-or-nothing (2).
   - Expected values come from the GDD (`drifters/10-electric-ball.md` Values, `08-difficulty.md` rows, `07-drifters.md` telegraph_min and warning size, `05-lives-and-damage.md` cooldown) and the contract's tables, written at the top of the file. The drop tick 202, the first firing state at y 288.1 and the log y 488.00 are worked out by hand from them.
4. **Assumptions:**
   - The refusal order is the code's and the spawner contract's: the missing x (start), then the seed (spawner step 8, before `born`), then in `born` the specialty, the variant's extra and the type's. The task text lists "a specialty, a seed" in that order; the test asserts the seed message when both are set, because the spawner raises it before `born` runs. Not a code bug; I note it only because the task text reads differently.
   - A ball hit on its first firing state is hit again on the first firing state of the next cycle (ticks_in_phase 360), not at the end of the 180-tick cooldown (tick 300), because that tick falls in a charge. The test asserts that, per Rules, Hitting again and run.md step 7.
   - Level 8 charge floor: no GDD value puts 84 under `telegraph_min` 45, so the floor is tested with a tuning charge of 30 and 60 and with `HazardRules(telegraph_min_ticks=100)`, as `test_chain_lightning.py` does.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer for the loader and tuning file work in `impact.md`; Architect's tasks DRA-111-04 (`test_collision.py`) and DRA-111-05 (`test_wave_files.py`, the telegraph guard) clear the remaining expected core failures. The task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (expected, `impact.md`: `test_collision.py` collection error until DRA-111-04; 5 `test_wave_files.py` cases until DRA-111-05; `test_electric_ball.py` 18 passed) · ui PASS (46)
QA: fail (core)
