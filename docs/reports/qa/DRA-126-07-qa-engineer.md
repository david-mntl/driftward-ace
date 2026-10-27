Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-126/tasks/DRA-126-07-qa-engineer.md`: the DRA-126 tests for the game flow (saves, message, picker, `saves_changed`, `stop_saves`, `best`, `leaderboard`, log lines), started by /implement.
2. **Delivered:** `game/tests/core/test_game_flow.py` (the DRA-125 logging test updated for the two flow lines on the game-over tick, and 12 DRA-126 test functions, 5 of them parametrized, 34 tests in the file), `game/tests/CONTEXT.md` (the file's paragraph), this report.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`: the whole `core` step passes (3406 tests) with the logging test `impact.md` names passing again, and `ui` (89 tests) passes. Every test on the task's `## Test` list is written, one behavior each: `start_flow` with and without saves; the opening for places 1 to 10, off the list and without saves; each opening setting all four fields again; the message constant while GAME_OVER shows; the picker's arrows (a lap of all 43 characters both ways, all 16 arrow combinations at three cursors); the saving confirm; the held confirm never picking RETRY; saves kept through RETRY, MENU and later runs; `stop_saves`; `best` and `leaderboard`; purity with saves; the new log lines in order and wording. To check the tests bite, I ran six one-line mutants of `game/core/game_flow.py` on a copy under the scratchpad (cursor direction flipped, `saves_changed` never set, `saves_changed` not cleared, picker kept across openings, `stop_saves` not clearing the flag, a wrong cursor log value). Each failed at least one test. No game code was touched.
4. **Assumptions:** A press that arrives while `picking` is True but `saves` is None (saves stopped on the screen) is not tested: the contract leaves it open. The code ends picking and saves nothing, and logs nothing. The Diagram's table cell "S+31 (up)" is read as the confirm key released, since "Up" would move the choice to MENU. The picker's character order is the GDD's `nickname_char_order`, a guess, written in the test from 11-save-data.md.
5. **Documentation differences:** None.
6. **Next:** the Integration Engineer (DRA-126-08, the views' tests, is a separate task). Pointer for the Director: the `name saved` log line writes `place=%s` in the code and the contract says `place=%d`. The output is identical for a saved name (the place is always a number then), so no bug and no test depends on it.
7. **Status:** done.

## Bugs
None open. Every new test passes against the code as it stands.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
