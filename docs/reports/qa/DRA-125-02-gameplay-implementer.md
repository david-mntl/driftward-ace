Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-02-gameplay-implementer (`core/game_flow.py`: screens, fresh-press rules, pause, RETRY, MENU, `add_flow_drifters`), Verify mode, started by /implement. The review is `Status: reviewed`.
2. **Delivered:** docs/reports/qa/DRA-125-02-gameplay-implementer.md. No test saved (Verify mode).
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core)`. Same state as after DRA-125-01: the 7 `retry_armed` typecheck errors and the 26 core tests that `impact.md` expects (see Harness). `env`, `lint`, `format` and `ui` pass. `game_flow.py` adds no failure (no mypy error names it, the core failures are the same 26 names as in the DRA-125-01 round).
   - Acceptance check reproduced inline (scratchpad script, `PYTHONPATH=. python`), every case of the task: the menu wraps both ways (up from Play gives Leaderboard, down from Leaderboard gives Play); Enter on Instructions and Leaderboard opens the page; a held Enter on a page does nothing; a fresh confirm goes back with Play selected. Enter held 40 ticks after Play: no pause, the run steps every tick (scroll ticks 1 to 40); released, pressed again: `pause by=key` then `screen paused`, run frozen. `focus_lost` pauses in play (`pause by=focus`), does nothing in the pause and on the menu. A pause in a respawn wait with ArrowUp pressed during the pause and held after the resume: still waiting; released then pressed: the wait ends. Last life with Enter and `focus_lost` given: the run steps, no pause; GAME_OVER with RETRY selected; down, down, up gives MENU, RETRY, MENU; Enter on MENU: `screen menu`, Play selected, no `new run`; Enter on Play: `new run` then `screen playing`, fresh run; lose again, Enter on RETRY: `new run`, PLAYING. `add_flow_drifters` with one meteorite: 0 added on a paused tick, a page tick and the resume tick, 1 added on a stepped tick.
   - Edge cases, all correct: up and down on one tick cancel on the menu and on GAME_OVER (no move, no log); confirm plus an arrow on one tick picks the old selection and leaves it unmoved (menu and GAME_OVER); confirm plus `focus_lost` on a PLAYING tick gives exactly `pause by=key`, `screen paused`; confirm held plus `focus_lost` gives `pause by=focus`; resume plus `focus_lost` on one tick resumes with no step; a confirm held through a resume does not re-pause and the next tick steps; 100 paused ticks leave the run equal to the pause tick's run and log nothing; left plus right in the pause change only `run.held`; `start_flow` with Enter or an arrow held does nothing until released and pressed again; Enter held through MENU at game over does not pick Play on the menu; Enter held through RETRY plays and never pauses; game over, MENU, Instructions, back, Play gives exactly one `new run`, logged before `screen playing`; the first Play logs no `new run`; invulnerability frozen across a pause; the tick before the last life with a confirm press pauses (the last life starts after it); confirm and focus ticks in the last life step the run each time; `add_flow_drifters` on the tick that enters GAME_OVER (`run_stepped` True, reviewer F1) returns the run unchanged and does not raise; `step_flow` leaves its input equal to a copy taken before; the same inputs twice (500 ticks across menu, pause, falls) give equal states.
   - The review's For QA list is covered: each of its five lines is in the checks above.
4. **Assumptions:** the 26 failing core tests and 7 typecheck errors are the ones `impact.md` and the DRA-125-01 QA report name as expected until DRA-125-09. F1 (`run_stepped` True on the tick that enters GAME_OVER) follows the tick flowchart; the contract's Rules sentence reads the other way for that one tick. No player effect, so not filed as a bug.
5. **Documentation differences:** None that block. For the Architect (not a bug): `systems/game-flow.md`, Rules, `run_stepped`, says False "after every tick that changed the screen", while the flowchart and the code leave it True on the tick that enters GAME_OVER. Proposed wording: "...False after every tick that changed the screen, except the tick that steps the run into game over."
6. **Next:** No bug is open and no fix is needed from the Gameplay Implementer. The verdict is `blocked` only because `check.sh` cannot end `QA: pass` until DRA-125-09 (QA Engineer) brings the 26 tests and 7 typecheck errors in line with `systems/run.md`. The Director or /implement decides whether to go on to the later tasks with these expected failures. Re-run this check (Re-test, appending a round) after DRA-125-09 lands; on a clean `QA: pass` it becomes `pass` and goes to the Integration Engineer.
7. **Status:** blocked: the harness is red only through failures a queued later task (DRA-125-09) clears.

## Bugs
None open. Nothing found in `game/core/game_flow.py`.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors: `retry_armed` in `test_run_waves.py:603,618,640`, `test_run_score.py:220`, `test_run_graze.py:921,933`, `test_coin.py:650`, all expected, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed after DRA-125-01's list, unchanged) · ui PASS (65 passed)
QA: fail (typecheck core)

## Round 2 2026-10-26

1. **Task:** Re-test of DRA-125-02-gameplay-implementer after DRA-125-09 landed (`docs/reports/qa/DRA-125-09-qa-engineer.md`, Verdict: pass), started by /implement.
2. **Delivered:** this round in docs/reports/qa/DRA-125-02-gameplay-implementer.md. No test saved.
3. **Checks:**
   - `check.sh`: env, lint, format, typecheck and core PASS. The 7 `retry_armed` typecheck errors and the 26 core failures of round 1 are gone. `ui` fails with the 3 `ui/test_game_over.py` tests (`test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty`), the ones `impact.md` clears with DRA-125-11. No other failure. `game/core/game_flow.py` is unchanged since round 1 and no `## Fix` section exists for this report, so there is no fix to re-check.
   - Acceptance check re-run inline (scratchpad `flow2.py`, `PYTHONPATH=. python`): Enter held at the start does nothing, released then pressed gives `screen playing`; Enter held 40 ticks after Play: no pause, scroll ticks 40; released, pressed: `screen paused`, run frozen over 50 paused ticks; confirm in the pause resumes (`run_stepped` False), held through the resume does not re-pause (next tick steps); `focus_lost` in play pauses, in the pause does nothing. The rest of round 1's cases (menu wrap, pages, respawn-wait pause, last life, GAME_OVER RETRY and MENU, `new run` once, `add_flow_drifters`) pass unchanged: `core/test_run_last_life.py` and the changed core tests now run green against the same `run.py`.
4. **Assumptions:** the 3 `ui` failures are expected until DRA-125-11, as the task brief and `impact.md` say. Nothing in them touches `game_flow.py`.
5. **Documentation differences:** same note as round 1, still for the Architect and not a bug: `systems/game-flow.md`, Rules, `run_stepped`, says False "after every tick that changed the screen", while the flowchart and the code leave it True on the tick that enters GAME_OVER. Proposed wording: "...False after every tick that changed the screen, except the tick that steps the run into game over." Pending approval.
6. **Next:** No bug is open and no fix is needed. Line 1 stays `blocked` only because `check.sh` ends `QA: fail (ui)` through the 3 `test_game_over.py` failures that DRA-125-11 (UI Developer) clears. Once DRA-125-11 lands and `check.sh` ends `QA: pass`, this report becomes `pass` and goes to the Integration Engineer. /implement can go on to DRA-125-10 and DRA-125-11 meanwhile.
7. **Status:** blocked: the harness is red only through failures a queued later task (DRA-125-11) clears.

### Bugs
None open. Round 1 had none.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui FAIL (3 failed, 62 passed, the three `test_game_over.py` tests expected by `impact.md`, cleared by DRA-125-11)
QA: fail (ui)

## Round 3 2026-10-26

1. **Task:** Re-test of DRA-125-02-gameplay-implementer after DRA-125-09 to DRA-125-12 landed, all `Verdict: pass`, started by /implement. Round 2 was blocked only because `check.sh` could not end `QA: pass`.
2. **Delivered:** this round in docs/reports/qa/DRA-125-02-gameplay-implementer.md. No test saved.
3. **Checks:**
   - `check.sh`: env, lint, format, typecheck, core and ui PASS (ui 89 passed, including the three `test_game_over.py` tests that failed in round 2). Last line `QA: pass`.
   - `game/core/game_flow.py` is unchanged since round 1 and the implementation report has no `## Fix` section for this QA report, so there is no fix to re-check.
   - Acceptance check re-run inline (scratchpad `flow2.py`, `PYTHONPATH=. python`): Play from the menu gives `screen playing`. Enter held 40 ticks after Play: no pause, scroll ticks 40. Released then pressed: `screen paused`, run frozen. Confirm in the pause resumes (`run_stepped` False), and the held confirm does not re-pause (next tick steps). `focus_lost` in play pauses, in the pause does nothing. Round 1's other cases (menu wrap, pages, respawn-wait pause, last life, GAME_OVER RETRY and MENU, `new run` once, `add_flow_drifters`) were re-checked by `core/test_game_flow.py` and `core/test_run_last_life.py`, which now run green.
4. **Assumptions:** the `run_stepped` wording difference is not a bug. The Director decided to keep the code as it is, because it follows the flowchart. The wording goes to the Architect later.
5. **Documentation differences:** same note as rounds 1 and 2, already decided by the Director: `systems/game-flow.md`, Rules, `run_stepped`, says False "after every tick that changed the screen", while the code leaves it True on the tick that enters GAME_OVER. The wording change is left to the Architect. Not a bug.
6. **Next:** the Integration Engineer. No bug is open.
7. **Status:** done.

### Bugs
None open. Round 1 had none.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (89 passed)
QA: pass
