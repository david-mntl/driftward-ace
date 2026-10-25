Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-117/tasks/DRA-117-07-qa-engineer.md`: the HUD tests brought in line with the GRAZE line, the `graze_text` tests, and the graze popup and ring view tests. Started by the main session.
2. **Delivered:**
   - `game/tests/ui/test_hud.py` (changed): the four tests `impact.md` lists now expect SCORE on line 1 and `GRAZE 0` on line 2 (`test_hud_line_two_is_empty_and_the_meters_are_gone` is renamed `test_hud_line_two_holds_the_graze_line_only_and_the_meters_are_gone`); six new GRAZE tests: place and look on line 2 in both modes with 0 to 12 digits, `GRAZE 0` for a fresh run, a 3-life run and a game-over run, SCORE and GRAZE each unmoved by the other, pixels follow the count and grow right, no overlap with the overlay, hearts or top line, and the render count (one render per new count, none for the same count, a new score never re-renders GRAZE).
   - `game/tests/ui/test_score_text.py` (changed): four `graze_text` tests (the contract's examples, 30 digits, grouping equal to `score_text` for 50 numbers, pure).
   - `game/tests/ui/test_graze_view.py` (new): 6 ring tests and 3 popup tests (graze color, coin color, same ink and place for both kinds, drawn where core puts it with the rise, ring outline on the ship's center, grows and fades on all 15 states, follows the ship, ring values honoured, nothing else drawn and the ship untouched, the GDD ring from `graze_ring`).
   - `game/tests/CONTEXT.md` (changed): the `test_score_text.py` and `test_hud.py` paragraphs updated, a paragraph for `test_graze_view.py`.
3. **Checks:** Before the edits `check.sh` ended `QA: fail (ui)` with 3 of the 4 `test_hud.py` failures `impact.md` lists (`score_is_on_line_one`, `line_two_is_empty`, `score_top_is_the_overlay_bottom_plus_the_gap`); `score_pixels_follow_the_score` passed but was brought in line too (it now measures line 1's ink only). After: `check.sh` ends `QA: pass`, 65 tests in `ui`, `test_graze_view.py` 9 of 9 passing, no failure from the impact table left. All expected values come from the contract, `06-scoring.md` and `drifters/04-coin.md`; the render count test patches the names `graze_text` and `score_text` in `ui.hud` (no private helper).
4. **Assumptions:** The ring's opacity is checked within 1 of `round(255 * opacity)` because SDL's alpha blend rounds; opaque rings are compared exactly. Ring radii that land on .5 are not used, since the contract says only "rounded". The `ui` step is slower (about 35 s for `test_hud.py`) because each HUD test reads whole 640 x 480 surfaces.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, for the app's draw order and the browser checks (out of scope here). No open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
