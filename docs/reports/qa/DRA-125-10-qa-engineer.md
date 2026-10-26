Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-125-10-qa-engineer (the game flow in `core.game_flow`: start, menu, pages, pause, last life, game over, `run_stepped`, `add_flow_drifters`, purity, logging), started by /implement.
2. **Delivered:**
   - `game/tests/core/test_game_flow.py` (new): 14 test functions, one per behavior of the task's `## Test` list, 29 cases with the parametrized ones.
   - `game/tests/CONTEXT.md`: a paragraph for the new file.
3. **Checks:**
   - `check.sh`: env, lint, format, typecheck and core PASS; all 29 cases of the new file pass in the `core` step. `ui` fails with the 3 `test_game_over.py` tests (`test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty`). Those are in `impact.md`, "Failures expected", cleared by DRA-125-11. Nothing else fails.
   - The tests catch real faults: I copied `game/` to the scratchpad and broke `game_flow.py` seven ways (no `hold_arrows` while paused, a pause allowed in the last life, `confirm_held` False at the start, the menu not reset to Play on entry, a confirm read as a press while held, `add_flow_drifters` adding on every tick, `pause by=` logged wrong when both happen). Each one fails a test of the new file. No game code was changed.
   - No `game/tuning/` file is read. Physics values (screen height, ship height, fall cap) are written at the top from the GDD, the last-life delay is a short test value (3), and no expected number is imported from the code under test. Menu and choice orders are written in the file from 02-game-flow.md.
4. **Assumptions:**
   - The tick that ends a run in game over: the code sets `run_stepped` True on it (it matches the tick flowchart: `run_stepped: True only after STEP`). The Rules sentence says it is "False after every tick that changed the screen". The two disagree on this one tick, so no test asserts the flag there. `add_flow_drifters` does nothing on it either way, because `add_drifters` returns a game-over run unchanged, and a test checks that.
   - "Run untouched" and "run unchanged" are checked with `==` on the frozen `Run`, not identity.
5. **Documentation differences:** One, pending approval. `docs/contracts/systems/game-flow.md`, Rules, `run_stepped`: "It is False after every tick that changed the screen, paused, resumed, started a run or stood on a page or the game-over screen" contradicts "True only after a tick on which `step_run` ran (PLAYING, the last life included)" and the flowchart for the tick that moves PLAYING to GAME_OVER. Proposed change: say "False after every tick that changed the screen, except the tick whose step ended the run in game over, where it is True", or have the code set it False there. No effect on play today. The Architect and the Director decide.
6. **Next:** Integration Engineer once DRA-125-11 clears the three `ui` failures; the Architect and the Director for the `run_stepped` wording above.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (`test_game_flow.py`: 29 passed) · ui FAIL (3 tests of `test_game_over.py`, expected until DRA-125-11)
QA: fail (ui)
