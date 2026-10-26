Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-117-06 (graze margin, graze state, graze popup and ring tests), started by /implement.
2. **Delivered:** `game/tests/core/test_graze_feedback.py` (new, 48 test cases from 9 test functions); `game/tests/CONTEXT.md` (a paragraph for the new file, before the `ui/test_score_text.py` line); this report.
3. **Checks:** `game/tests/check.sh`: env, lint, format, typecheck and core PASS, with the new file in the `core` step and all 48 cases passing. `ui` fails on exactly the three `test_hud.py` tests that `docs/contracts/DRA-117/impact.md` lists as expected until DRA-117-07 (`test_hud_score_is_on_line_one_at_the_left_margin`, `test_hud_line_two_is_empty_and_the_meters_are_gone`, `test_hud_score_top_is_the_overlay_bottom_plus_the_gap`). No other failure. Mutation check on a scratch copy of `game/core` (not the repo): opacity step off by one, popup x moved 1 px, a ring kept one state too long and `GRAZE_MARGIN` 15 each fail the new tests (12 to 17 cases each).
   Covered, one test per behavior of the task's `## Test` list:
   - Margin from the spawner: all five drifter types and `born_drifter`, default and tuned (20.0, 3.5); zone is the hitbox grown by it for circle, box, line and polygon (written out from 06-scoring.md rule 3), at every position as the rock moves, `()` in the warning; a 1 px probe just inside and just outside the margin from each shape's own edge; no change with level, `as_level` or the switches; chain lightning and electric ball while firing, `()` while charging.
   - Graze state: every new drifter OUTSIDE; `update` keeps INSIDE, OUTSIDE and SPENT through two whole cycles.
   - Popup: kind GRAZE, at the ship's center after its move on the paying tick (checked against `core.ship.step`), the points, rises by the rules' rise, shown on exactly `popup_ticks` states and gone after; a coin's popup keeps kind COIN, also on the same tick as a graze (coin first).
   - Ring: age 0 at start size and opacity 1.0, even step in size and opacity, opacity above 0 on every state shown, exactly `ring_ticks` states; `step_graze_rings` order and drop.
   - Rules: the GDD defaults `GrazeRules()`, a custom set, a 1-tick set (points 0, rise 0) and a long set, direct and inside a run.
   - Aging in the respawn wait, on protected ticks and in both.
   - `GrazeRules()` against the GDD's seven values, `DEFAULT_GRAZE_RULES` and the `DEFAULT_GRAZE_*` constants.
4. **Assumptions:** The test meteorite variants (`circle`, `box`, `line`, `polygon`) use test sizes, not the game's: only the grow rule is under test. A polygon's zone is written as the polygon followed by one line per edge of thickness twice the margin, from `grow_hitbox`'s contract. The three `ui` failures are accepted as expected per `impact.md`, so the task's acceptance check (`QA: pass` once those are cleared) is met for everything in this task's scope.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer once DRA-117-07 has cleared the three expected `test_hud.py` failures and the `check.sh` last line reads `QA: pass`. No bug open.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (48 new cases in `test_graze_feedback.py`) · ui FAIL (only the 3 `test_hud.py` tests listed in `impact.md`, cleared by DRA-117-07)
QA: fail (ui)
