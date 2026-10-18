Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-61-02-ui-developer (`game/ui/score_text.py`, and the SCORE line the implementer also put in `game/ui/hud.py`), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-61-02-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: **QA: fail (ui)**. lint, format, typecheck, core pass. ui: 33 passed, 2 failed (`test_hud_normal_layout_leaves_line_one_empty`, `test_hud_keeps_the_gap_below_the_overlay`). The task's acceptance check needs `check.sh` to end `QA: pass` with every existing test unchanged. It does not. See B1.
   - Acceptance command, run from `game/` unchanged, prints `['SCORE 0', 'SCORE 999', 'SCORE 1 000', 'SCORE 1 234', 'SCORE 1 000 007', 'SCORE 1 234 567']` and `False` (no pygame imported). Matches the task.
   - `score_text` edge cases (inline): 0, 1, 9, 10, 99, 100, 999, 1000, 9999, 10000, 99999, 100000, 999999, 1000000, 10**9, 10**30+7, 10**100. Every one starts `SCORE `, has groups of exactly 3 after a first group of 1 to 3, no double space, no leading zero, and equals `f"{n:,}"` with commas turned into spaces. No digit limit holds.
   - Review For QA lines, run against the HUD code as it now stands (the code B1 says belongs to task 06):
     - Normal mode, score 0: ink starts at x 4, rows 5 to 12, so SCORE is on line 1 at (4, 4). Debug mode: first ink row 57, `overlay_text_bottom() + 4` is 56, so no overlap.
     - Hearts: lives 3, 2, 1, 0 fill slots (608, 576, 544) as 3, 2, 1, 0 hearts. They don't move.
     - Cache: same score twice reuses the same surface object. Score 0, then 11, then 0 re-renders each time (misses 3, maxsize 1, currsize 1), so retry back to `SCORE 0` re-renders.
     - `pygame.quit()` then `pygame.init()` then `draw_hud`: no error. Run `repr` is identical before and after a draw.
     - The score of `Scroll(ticks=130, scrolled_ticks=100)` is 11.
   - Review: 0 open findings (F1 fixed, round 2 re-check clean).
4. **Assumptions:** The task file and the contract's Impact table are the authority on what this task builds. They give `game/ui/hud.py` to task `DRA-61-06-ui-developer`, not to this task.
5. **Documentation differences:** None. The contract and task agree with each other; the code does not follow them.
6. **Next:** UI Developer, Fix mode, bug report `docs/reports/qa/DRA-61-02-ui-developer.md` (B1). After the fix the QA Engineer re-tests. Director note: tasks DRA-61-05 (rewords the two tests) and DRA-61-06 (the SCORE line in `hud.py`) are the order the contract sets.
7. **Status:** done.

## Bugs
- **B1** `game/ui/hud.py:1-128` (the whole diff against `HEAD`), UI Developer. The task builds only `game/ui/score_text.py`. Its Out of scope says "The HUD's SCORE line and `game/ui/hud.py` (task DRA-61-06)". The implementer also changed `hud.py`: SCORE on line 1, the meters readout removed. That breaks two existing tests before task DRA-61-05 rewords them.
  Reproduce: `game/tests/check.sh ui`, or `game/tests/check.sh ui -k "line_one_empty or gap_below_the_overlay"`.
  Expected: `QA: pass`, every existing test passing unchanged, with `game/ui/hud.py` as it is at `HEAD` (meters readout on line 2, line 1 empty).
  Actual: `QA: fail (ui)`. `test_hud_normal_layout_leaves_line_one_empty`: `assert 5 >= 24` (ink at row 5, expected at or below line 2). `test_hud_keeps_the_gap_below_the_overlay`: `assert 57 >= ((52 + 4) + 20)`.
  Source: `docs/contracts/DRA-61/tasks/DRA-61-02-ui-developer.md` (Builds, Acceptance check last paragraph, Out of scope); `docs/contracts/systems/hud.md`, Impact (the DRA-61 table: the two-step order, `hud.py` is task DRA-61-06, the two tests are reworded first by DRA-61-05); hud.md, Rationale ("The HUD tests change in two steps").
  Proposed fix: restore `game/ui/hud.py` to `HEAD` (`git checkout game/ui/hud.py`), and keep `game/ui/score_text.py` as it is. Task 06 re-applies the SCORE line after task 05 lands. The code in the working tree already does what hud.md says for the SCORE line (checked above), so task 06 can reuse it unchanged. This keeps `check.sh` at `QA: pass` after this task, as the contract's two-step order requires.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui FAIL (33 passed, 2 failed)
QA: fail (ui)

## Round 2 2026-10-18

1. **Task:** Re-test of B1 on DRA-61-02-ui-developer, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-61-02-ui-developer.md (this round appended, line 1 now `Verdict: pass`).
3. **Checks:**
   - B1 reproduce: `game/tests/check.sh ui` now gives 35 passed, 0 failed, including `test_hud_normal_layout_leaves_line_one_empty` and `test_hud_keeps_the_gap_below_the_overlay`. `git diff HEAD -- game/ui` is empty and `git status` shows `game/ui/hud.py` unmodified, so only `game/ui/score_text.py` is new in `game/ui/`.
   - `game/tests/check.sh`: env, lint, format, typecheck, core (1334 passed), ui (35 passed) all PASS. Last line `QA: pass`. No test file changed.
   - Acceptance check, run unchanged from `game/`: prints `['SCORE 0', 'SCORE 999', 'SCORE 1 000', 'SCORE 1 234', 'SCORE 1 000 007', 'SCORE 1 234 567']`, and `'pygame' in sys.modules` is `False`.
   - Neighbor check after the review-fix edit at `score_text.py:34`: `score_text(n)` equals `"SCORE " + f"{n:,}"` with commas turned into spaces for every n in 0..2999, for 10^k-1, 10^k, 10^k+1 and 10^k+7 for k 3..39, and for 10^100. 0 mismatches.
   - Grep of `game/ui/score_text.py` for sleep, threading, asyncio, pygame.display, pygame.event, image.load, mixer: no hits.
4. **Assumptions:** The SCORE line and the `hud.py` edit belong to tasks DRA-61-05 and DRA-61-06, as in round 1. The HUD checks from round 1 (line 1 position, hearts, cache, quit and init) described the reverted `hud.py` and no longer apply to this task.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Task DRA-61-06 re-applies the SCORE line after DRA-61-05 rewords the two HUD tests.
7. **Status:** done.

## Bugs
- **B1** fixed. `game/ui/hud.py` is back at `HEAD`; the two tests pass unchanged.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (1334) · ui PASS (35)
QA: pass
