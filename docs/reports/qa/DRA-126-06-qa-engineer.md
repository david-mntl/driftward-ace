Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-126-06-qa-engineer (saves tests and the level-reached tests), started by the /implement skill.
2. **Delivered:** `game/tests/core/test_saves.py` (new, 47 test cases from 14 test functions), `game/tests/core/test_run_last_life.py` (4 new tests at the end, module docstring line added), `game/tests/CONTEXT.md` (a paragraph for `test_saves.py`, a sentence for the new `test_run_last_life.py` tests).
3. **Checks:** `check.sh` env, lint, format, typecheck and ui PASS. The `core` step has 3339 passed and 1 failed: `test_game_flow.py::test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`. That is the one failure `docs/contracts/DRA-126/impact.md` lists as expected until DRA-126-07 (the flow now logs `game over message=game_over place=none` before `screen game_over`). Every new test passes against the code (`check.sh core -k "saves or last_life"`: PASS). Mutation check on a scratch copy (never in the repo): changing the tie rule `>=` to `>` in `place_of` fails 2 saves tests; setting `final_level=None` in `_start_last_life` fails 5 level tests. One test per bullet of the task's `## Test` list: order and place; `place_of` limits; `message_for`; `add_entry`; `best`; nickname; picker (`start_picker`, `turn_character`, `move_cursor`, `picked_name`); purity (marked `determinism`); `final_level`, `level_reached` and `next_run`.
4. **Assumptions:** The character order is the GDD's guess (`nickname_char_order`); `test_saves.py` writes it from the GDD, so a change of order fails the constants test first. `add_entry` on a list with no place is not tested (the contract says the caller never does it). A game-over state has `last_life` False, so the level test reads `lives == 0` there. Game over is on tick L + delay, so the last life has L + delay + 1 states.
5. **Documentation differences:** None.
6. **Next:** The Integration Engineer's gate still waits on DRA-126-07 (it clears the one expected `test_game_flow.py` failure) and DRA-126-08. The Architect decides on the task close-out; the task file stays `Status: open`.
7. **Status:** done.

## Bugs
None. The one failing test is the expected failure in `impact.md` (cleared by DRA-126-07), not a bug against this task.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1 expected: `test_game_flow.py` log-order test, cleared by DRA-126-07) · ui PASS
QA: fail (core)
