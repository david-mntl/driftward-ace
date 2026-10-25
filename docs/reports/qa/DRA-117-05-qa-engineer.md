Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-117-05 (the graze rule inside the run), `docs/contracts/DRA-117/tasks/DRA-117-05-qa-engineer.md`, started by the Director.
2. **Delivered:**
   - `game/tests/core/test_run_graze.py` (new): 22 test cases from 17 test functions, one per behavior in the task's `## Test` list.
   - `game/tests/CONTEXT.md`: a paragraph for the new file.
   - `game/tests/core/test_ufo.py` (changed): `test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds` failed from DRA-117-02 only because a touched UFO now has `graze_state` SPENT (run.md, step 5b item 3), while its untouched twin is OUTSIDE. It now asserts SPENT and compares the UFO with its twin apart from that field. `impact.md` allows this change under Builds.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and core pass (3183 core tests). `test_run_graze.py` is in the core step and all 22 cases pass.
   - The `ui` step fails on exactly three tests, all in `impact.md`'s expected-failure table, cleared by DRA-117-07: `test_hud_score_is_on_line_one_at_the_left_margin`, `test_hud_line_two_is_empty_and_the_meters_are_gone` and `test_hud_score_top_is_the_overlay_bottom_plus_the_gap`. They are not bugs of this task. The table's fourth test, `test_hud_score_pixels_follow_the_score`, passes.
   - Mutation check, inline on a copy in the scratchpad, never on the game code: (a) `may_pay` ignored, (b) off-screen drifter keeps its zone, (c) a touch not marking SPENT, (d) a blocked exit marking SPENT. Each is caught by the test named for that rule.
   - No bug found in `core/graze.py` or `core/run.py`: every expected value in the tests matched the code on the first run, apart from my own scene mistakes, which I fixed in the tests.
4. **Assumptions:**
   - The ship is put back at rest on its home spot before each tick (a ship held still, flying and hovering) and the hazard is moved by its gap to the ship's foot. The foot (32 x 12 at the bottom of the 32 x 32 square, 04-ship.md) is worked out in the file. Gaps of 6 and 20 px, and -4 px for a touch, sit well clear of the 14 px margin, so the ship's 0.16 px fall per tick never decides a result.
   - The chain lightning is tested through its flat pair, the one variant that exercises the rule. The rule lives in the base, not in a layout.
   - `test_a_graze_on_a_fall_tick...` puts `Ship(320, 495, vy=5.5)` on the tick that falls, as `test_coin.py` does.
   - A ship that really hovers by thrust is not built. Every scene here holds the ship still, which is the contract's "hovering in place".
5. **Documentation differences:** None.
6. **Next:** Integration Engineer once the `ui` expected failures are cleared by DRA-117-07. DRA-117-06 and DRA-117-07 (QA test tasks) are still to run. Nothing for the Gameplay Implementer.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3183 passed) · ui FAIL (the three expected failures above, cleared by DRA-117-07)
Last line: `QA: fail (ui)`. Verdict is `pass` because the only failing step is the expected failures `impact.md` lists for DRA-117-07, and the task's acceptance check names that case. Core, with `test_run_graze.py`, passes in full.
