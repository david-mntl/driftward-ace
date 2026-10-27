Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-126-08 (UI tests for the saves: group_digits and best_text, BEST on the HUD, the game-over message and picker, the leaderboard rows), started by the /implement skill.
2. **Delivered:**
   - `game/tests/ui/test_score_text.py` (3 tests added)
   - `game/tests/ui/test_hud.py` (6 tests added)
   - `game/tests/ui/test_game_over.py` (9 tests added)
   - `game/tests/ui/test_leaderboard.py` (5 test functions added, 7 cases with the parametrized one)
   - `game/tests/CONTEXT.md` (the four files' paragraphs)
3. **Checks:** `game/tests/check.sh` ends `QA: pass`; the `ui` step runs 115 tests, all passing, and every earlier test still passes. Each `## Test` line has a test: grouping and `best_text`; BEST at `HUD_BEST_X` on line 1 in both modes, nothing for None, the old call unchanged; BEST rendered again only when `best` changes; the message in the title's place and the DRA-125 calls; the picker layout (box, six lines, ten cells, characters, underline, blank); the cursor outline and hint while picking and the screen after the save; the leaderboard rows (one row per entry, four aligned columns, table centered, rows 24 px apart, footer in place, no entries is the DRA-125 page); the same pixels twice with nothing changed but the surface. I also ran six deliberate breaks of the UI code in a scratch copy (BEST one row low, the outline on the wrong cell, grey labels left white, the score column left-aligned, row spacing 25, the label `BEST:`). Each one failed a new test. The scratch copy is not in the repo.
4. **Assumptions:**
   - The table's left edge is checked at the floor or the ceiling of the centered position, and the leaderboard title's top within 1 px of centered, because the contract says "centered" and does not fix the rounding. Same 1 px slack for the picker's cells and characters, as the existing page tests allow.
   - The hint's ink starts on the row right under the slot row, so while picking the two are read as one band and the hint by its rows.
   - The stand-in values (picker box 400 x 280, 24 px characters, the hint text, grey 128, rows 24 px apart, columns 24 px apart) are written at the top of each file from scope report DRA-126, Values needed, and the away log, Decisions 4 and 5. The character order is the GDD's guess.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. All DRA-126 UI tasks (03, 04, 05) and their tests (06, 07, 08) are now QA-passed.
7. **Status:** done.

## Bugs
None. Every new test passes against the code.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
