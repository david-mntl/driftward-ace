Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-03-ui-developer (`game/ui/burst_view.py`: `draw_burst`, `BURST_COLOR`), Verify mode, started by /implement. The review is `Status: reviewed`.
2. **Delivered:** docs/reports/qa/DRA-125-03-ui-developer.md. No test saved (Verify mode).
3. **Checks:**
   - `game/tests/check.sh`: env, lint and format PASS, ui PASS (65 passed). typecheck and core FAIL, both only in the failures `docs/contracts/DRA-125/impact.md` expects from DRA-125-01 (see Harness). Nothing in `game/ui/burst_view.py` fails.
   - Acceptance check reproduced inline (scratchpad script `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa_burst.py`, black 640 x 480, 8-connected blobs, `repr(burst)` the same before and after each draw):

     | Burst | opacity | blobs | radius (px) | max channel | px per blob |
     |---|---|---|---|---|---|
     | (320,240) age 0 | 1.0 | 1 (all 12 squares on the origin, core's rule) | 0.7 | 255 | 9 |
     | (320,240) age 30 | 0.75 | 12 | 29.3 to 30.5 | 191 | 9 |
     | (320,240) age 60 | 0.5 | 12 | 59.4 to 60.5 | 128 | 9 |
     | (320,240) age 119 | 0.0083 | 12 | 118.5 to 119.5 | 2 | 9 |
     | (320,480) age 30 | 0.75 | 7 (lower half off the canvas) | 29.3 to 30.5 | 191 | 9 or 6 |

   - Edge cases, all correct:
     - Fade: on ages 10 to 119 the brightest pixel equals `round(255 x opacity)` on every age (234, 212, 191 ... 21, 2) and never rises. Age 120 (finished, opacity 0.0) draws nothing.
     - Placement: on age 10, every one of the 12 squares has all 9 pixels lit at top-left `(round(cx - 1.5), round(cy - 1.5))`.
     - Cache: `_square_image(3, 100)` returns the same object twice. Drawing ages 0 to 120 gave 121 entries, one per alpha, inside the contract's "few hundred".
     - Custom `LastLifeRules`: size 1, size 10 with count 1, size 4 with count 4 and speed 2.5 over 7 ticks, and speed 0 with delay 1. Blob counts, sizes and fade are right and nothing shows at the finished age.
     - Off screen: centers at (-50,-50) and (700,600) draw without error and change nothing outside.
     - Surface use: on a gray (100,100,100) background the only change is the squares, and a half-opaque square gives 178 (100 + 155 x 0.5 rounded). On a (7,8,9) surface the corner pixel is unchanged, so the view never fills.
     - Same burst drawn twice: identical bytes.
     - In a real run (`lives=1`, a fall): the burst starts on tick 1 at (320.0, 480) with `run.last_life` True, stays at that origin for all 120 ticks while the scroll moves 100.1 px, equals a burst rebuilt from `start_burst` and `step_burst` at every age, and game over comes 120 ticks later with opacity 0.0.
   - The review's **For QA** line on the 8 unnamed core failures: all 26 core failures read, 10 of them (every one the implementer calls unnamed, plus the logging test) re-run with `--tb=short`. Each fails because the last-life tick is not game over: `assert over.game_over` False, `lives == 0` on a retried run, the score 90 against 91 after the freeze, or the log lines `last life score=95` and `game over score=95` in a test that expects no score line. This is the general rule in `impact.md`. None points at a bug in DRA-125-01, so none is filed. DRA-125-09 brings them in line.
   - Review finding F1 (the acceptance check says 12 blobs at age 0, core puts all squares on the origin): the code follows the contract. Not a bug.
4. **Assumptions:** The 26 core and 7 typecheck failures are accepted as expected, because the task's acceptance check allows exactly the failures `impact.md` lists or covers by its general rule. A run of `check.sh` therefore ends `QA: fail (typecheck core)` and not `QA: pass`.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, for the burst view. DRA-125-09 (QA Engineer) must bring the 26 core tests and the 7 typecheck errors in line, including the 8 or so tests `impact.md` names only by its general rule. The task's acceptance wording "12 blobs" at age 0 is for the Architect to correct (review F1). The QA report for DRA-125-01 is a separate verdict.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`, all `retry_armed`, expected from DRA-125-01, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed; all in `test_coin.py`, `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py`, `test_run_waves.py`, all from the DRA-125-01 last-life tick, cleared by DRA-125-09) · ui PASS (65 passed)
QA: fail (typecheck core)
