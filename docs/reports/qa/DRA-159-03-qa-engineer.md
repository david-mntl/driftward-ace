Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-159/tasks/DRA-159-03-qa-engineer.md`: tests for the mute icon view, the shipped picture and the tuning rectangle, started by the Director's session.
2. **Delivered:** `game/tests/ui/test_mute_icon.py` (new, 7 tests, one per behavior in the task's `## Test` list); `game/tests/CONTEXT.md` (one line for the new file).
3. **Checks:**
   - `check.sh ui -k mute_icon -v`: 7 passed, `QA: pass`.
   - Full `check.sh`: env, lint, format, typecheck, ui PASS (895 ui tests). core FAIL with exactly one test, `test_drifter_registration.py::test_only_a_drifters_own_modules_name_its_type` (3498 passed, 1 failed). That is the known `tools/wave_editor/bench.py:302` edit (B1 of `docs/reports/qa/DRA-159-02-ui-developer.md`), unrelated to this task and not counted. No other test fails.
   - Tests read `margin` 8 and `size` 24 from `tuning/mute_icon.json`, the window 856 x 518 and the play area corner from `tuning/hud.json`, and the play area size from `core.world`. No number is invented.
   - Tests and the picture pass `ruff check`, `ruff format --check` and `mypy --strict`.
4. **Assumptions:**
   - The tests read the two JSON files directly, not `app.mute_icon_tuning`, which does not exist yet and is out of scope (task: no tests for the loader).
   - "Must not touch the play area" (Loading 15) is tested as no shared pixel (`Rect.colliderect` is False). Edge-adjacent rectangles would pass. The current values leave a gap, so this does not matter today.
   - The window and play area are the 856 x 518 and 640 x 480 at `field_x`/`field_y` of `hud.json`, as the task says.
5. **Documentation differences:** None.
6. **Next:** The Integration Engineer can proceed on this task. Core is still red from B1 of the DRA-159-02 report (owner named there).
7. **Status:** done.

## Bugs
None open for this task. The new tests pass against `game/ui/mute_icon.py`, `game/tuning/mute_icon.json` and `game/assets/mute_icon.png`.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, `test_only_a_drifters_own_modules_name_its_type`, unrelated, see B1 in DRA-159-02) · ui PASS
QA: fail (core)
The new file alone: 7 passed, `QA: pass`.
