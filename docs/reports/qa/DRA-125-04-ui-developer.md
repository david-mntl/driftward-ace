Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-04-ui-developer (`game/ui/screen_look.py`, `game/ui/menu.py`: `draw_menu`, the menu constants and `screen_font`), Verify mode, started by /implement. The review is `Status: reviewed` (F1 and F2 are notes, no action).
2. **Delivered:** docs/reports/qa/DRA-125-04-ui-developer.md. No test saved (Verify mode).
3. **Checks:**
   - `game/tests/check.sh`: env, lint and format PASS, ui PASS (65 passed). typecheck and core FAIL, both only in the failures `docs/contracts/DRA-125/impact.md` expects from DRA-125-01 (see Harness). Nothing in `game/ui/screen_look.py` or `game/ui/menu.py` fails.
   - Acceptance check reproduced: `accept2.py` (the implementer's script, scratchpad) run again, and an independent script `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa04/qa.py` that works the expected places out from the fonts (title `get_linesize()` 24, item `get_height()` 16, `size(" ")` 4) and reads the ink from the pixels. PNGs the Director can open are in `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-04/` (`menu_play.png`, `menu_instructions.png`, `menu_leaderboard.png`).

     | Line on 640 x 480 | ink rows | ink cols | ink center_x |
     |---|---|---|---|
     | title | 170-186 | 227-413 | 320.0 |
     | Play | 217-232 | 305-336 | 320.5 |
     | Instructions | 257-268 | 270-370 | 320.0 |
     | Leaderboard | 297-308 | 268-372 | 320.0 |

     Expected from the contract: block 2 x 24 + 2 x 40 + 16 = 144, top (480 - 144) // 2 = 168, item rect tops 216, 256, 296 (ink is 1 to 2 px lower for glyph bearing). Matches: item tops 40 apart, one blank title line (24 px) under the title. Marker ink (selection Play, Instructions, Leaderboard): rows 221-229, 261-269, 301-309, always inside the selected item's rows, cols 291-298, 256-263, 254-261, always left of the label; the marker rect's right edge is exactly the label's left edge minus 4 (the space). No marker ink on the other two items.
   - Edge cases, all correct:
     - Other sizes (800 x 600, 641 x 481, 320 x 300, 1000 x 200, 1280 x 720): the block re-centers both ways (top = (h - 144) // 2 each time), title center_x is `width // 2` each time (an odd width rounds down, as the contract says), the marker is left of the label in the selected rows each time. A 50 x 50 surface and a SRCALPHA surface draw without error.
     - Selection switch: the common ink of the three images is only the four text lines; each selection adds only its marker. Play against Leaderboard differs only in the two item rows (221-229 and 301-309). The labels never move.
     - Same selection drawn twice: identical bytes. Same on a gray (100,100,100) background: the ink positions equal the black one's and the corner pixel is untouched, so the view never fills.
     - Cache: `_render` 5 misses for 5 distinct (text, size) pairs, `screen_font` 2 misses (32 and 24). After 150 more draws the misses are still 5 and 2. `screen_font(24) is screen_font(24)`.
     - Look: white, antialiased (max channel 255). No `log.*` call in either file. `ui.screen_look` imports pygame only and loads no `core` module. `game/core/` and `game/app/` have no change from this task.
   - Review **For QA**, last line (26 core failures): all 26 listed and re-run with `--tb=short`, including the unnamed ones (`test_a_held_arrow_never_retries`, `test_a_new_run_starts_like_the_first`, `test_a_fall_and_a_touch_on_one_tick_cost_only_the_fall`, `test_no_playing_tick_changes_the_coin_points`, `test_the_waves_step_once_on_every_playing_tick`, `test_a_graze_and_a_hit_by_another_hazard_on_one_tick_the_graze_pays_then_the_hit_counts`, `test_the_same_first_seed_gives_the_same_run_of_waves_and_retries`). Each fails because the last-life tick is not game over (`assert over.game_over` False after a fall, the score 90 against 91, `lives == 0`, or the log lines `last life score=95` and `game over score=95`). That is the general rule in `impact.md`, DRA-125-01. The set is the same 26 as in the DRA-125-03 report. None points at a bug, so none is filed. DRA-125-09 brings them in line.
4. **Assumptions:** The 26 core and 7 typecheck failures are accepted as expected, as in the DRA-125-03 report, because the task's acceptance check allows exactly the failures `impact.md` lists or covers by its general rule. A run of `check.sh` therefore ends `QA: fail (typecheck core)` and not `QA: pass`.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, for the menu view. DRA-125-09 (QA Engineer) must bring the 26 core tests and the 7 typecheck errors in line. Review F1 (a shared marker helper for DRA-125-08) is for the Architect when DRA-125-08 lands.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`, all `retry_armed`, expected from DRA-125-01, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed; all in `test_coin.py`, `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py`, `test_run_waves.py`, all from the DRA-125-01 last-life tick, cleared by DRA-125-09) · ui PASS (65 passed)
QA: fail (typecheck core)
