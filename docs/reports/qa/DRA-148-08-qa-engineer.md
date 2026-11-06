Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-148-08 (the level-up banner inside `core.run`), `docs/contracts/DRA-148/tasks/DRA-148-08-qa-engineer.md`, started by the Director's pipeline.
2. **Delivered:** `game/tests/core/test_run_level_up.py` (new, 25 test cases from 10 test functions, two parametrized), `game/tests/CONTEXT.md` (one paragraph added for the new file). QA report: `docs/reports/qa/DRA-148-08-qa-engineer.md`.
3. **Checks:** `game/tests/check.sh` ends `QA: pass` (env, lint, format, typecheck, core, ui all PASS; 786 tests in the last full run, `test_run_level_up.py` in the `core` step, all its cases passing). Three mutations of `core.run`, run inline and not saved, each failed the new tests as they should: the HUD switching one tick late (`age <= arrival`), the banner living one tick too long, and step 9b ignoring the burst (last-life tests fail). One test per behavior of the task's `## Test` list:
   - start at age 0 with previous level and level, one tick older each state, over seven rises;
   - the cue on the rise state only, and rest 0 or no rules giving no banner and no cue while the level still rises;
   - `hud_level` previous until the arrival age and real from it, with `run.level`, the scroll step (1.1 x 1.1 at Level 2 on the next ticks) and `level_reached` real at once;
   - None at the lifetime, through Wave 0's end, at Level 8 and for a run with no waves;
   - a skipped level (previous level 1, level reached shown, never the passed level);
   - pause through `step_flow` (paused states with arrows and a focus loss keep the banner, a resume then steps it one tick), at five ages;
   - a hit or a fall equal to an untouched twin tick by tick, at four ages;
   - the last life lost during the banner (age 0 and 2), a rise on a later last-life tick, and a rise on the very tick it is lost: banner None, no cue, `hud_level == level`;
   - a game-over tick (None, and a banner put on the state is unchanged), `next_run` from game over, the last life and mid-banner (None, same rules, the same banner again on tick 50; rest 0 carries too);
   - the respawn wait and protected ticks aging the banner like the twin on every tick, with the rise inside the wait.
4. **Assumptions:** the level-up values in the file (rest 20, arrival 6, banner 14) are test-local and obey the contract's limits, because the task says the file reads no `game/tuning/` file. The Level 8 case adds a pool wave to the book so the run can go on after Level 8's last wave, as the loader would demand. The game-over test puts a banner on a game-over state by `replace` to show the tick leaves it alone (run.md, a game-over tick).
5. **Documentation differences:** None.
6. **Next:** Implementation work for DRA-148-09 (views and HUD) is the next task; nothing from this task is open for the Gameplay Implementer. The Integration Engineer's gate also needs the UI tasks' QA reports.
7. **Status:** done.

## Bugs
None. Every new test passes against `game/core/run.py`, `game/core/waves.py` and `game/core/level_up.py` as they are.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
