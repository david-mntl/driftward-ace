Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the SCORE line and `score_text` from `docs/contracts/DRA-61/tasks/DRA-61-02-ui-developer.md` (contract `docs/contracts/systems/hud.md`, v2), asked by the Architect.
2. **Delivered:**
   - `game/ui/score_text.py` (new): `SCORE_LABEL`, `DIGIT_GROUP`, `GROUP_SEPARATOR`, `score_text`.
   - `game/ui/hud.py` (changed): SCORE on HUD line 1 from `run.score`, line 2 empty, meters readout gone, text re-rendered only when the score changes, module and `draw_hud` docstrings name SCORE.
3. **Checks** (from `game/`, `PYGAME_HIDE_SUPPORT_PROMPT=1`):
   - IS_CE: `python -c "import pygame; assert pygame.IS_CE"` passes (asserted inside the draw run below).
   - Acceptance command from the task, run unchanged, prints:
     `['SCORE 0', 'SCORE 999', 'SCORE 1 000', 'SCORE 1 234', 'SCORE 1 000 007', 'SCORE 1 234 567']`
     `True True True`
   - Screenshot run: `draw_debug_overlay(surface, spawn())`, then `draw_hud(surface, Run(ship=spawn(), scroll=Scroll(ticks=130, scrolled_ticks=100), lives=3), True)` on a 640 x 480 surface, saved with `pygame.image.save`. Image: `/tmp/claude-1000/-workspace/560f3b16-f48a-4957-8e50-a98c857bb711/scratchpad/hud_debug.png`. It shows `SCORE 11` below the green overlay text and three hearts at the top right.
   - Follows the state: score 11 drew 274 ink pixels in the SCORE area, a score of 10 000 drew 400 (a longer text). With 3 lives the heart at slot 2 (x 552, y 16) is white, with 2 lives it is black. Run repr and score identical before and after a draw.
   - `game/tests/check.sh lint`: PASS lint, PASS format. `game/tests/check.sh typecheck`: PASS.
   - `game/tests/check.sh ui`: 33 passed, 2 failed. The two expected failures, until task DRA-61-05 (contract, Impact): `test_hud_normal_layout_leaves_line_one_empty` and `test_hud_keeps_the_gap_below_the_overlay`. No test edited.
   - Grep of `game/ui/hud.py` and `game/ui/score_text.py` for sleep, threading, asyncio, pygame.display, pygame.event, pygame.key, image.load, mixer, `random.random(`, .mp3, .wav: no hits. Grep of `game/core/` for `game.ui` or `ui` imports: no hits.
4. **Assumptions:** None beyond Decisions.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-61/tasks/DRA-61-02-ui-developer.md`. Left alone: `game/ui/game_over.py` (task DRA-61-03), `game/ui/debug_overlay.py`, all tests.
7. **Status:** done.

## Decisions
- `score_text` groups digits by hand with `DIGIT_GROUP` and `GROUP_SEPARATOR` instead of `f"{n:,}"`, so the contract's constants are the single source of the format. Leftmost group is `len % 3 or 3` digits.
- The rendered SCORE surface is cached with `lru_cache(maxsize=1)` on `_score_surface(score)`: it re-renders only when the score differs from the last one, and holds one surface, never a growing cache. Same pattern as the existing `@cache` font and heart helpers in the file. Source: hud.md, SCORE line; 15-tech-constraints.md, rule 5.
- Constants (`HUD_COLOR`, `HUD_FONT_SIZE`, `HUD_MARGIN`, `HUD_LINE_SPACING`, `HUD_TOP`, `HUD_OVERLAY_GAP`) are unchanged, from hud.md, Interface. `HUD_LINE_SPACING` is now unused by `draw_hud` (line 2 is empty) but the contract keeps it, so it stays. Their docstrings say "HUD text" instead of "Readout".
- `score_text.py` imports only `logging` and has its `log`, as the contract and game/CONTEXT.md ask.

## Review fix 2026-10-18: docs/reports/review/DRA-61-02-ui-developer.md

Fixed: DRA-61-02-F1

1. **Task:** Answer review finding DRA-61-02-F1 (round 1), asked by the `/implement` skill.
2. **Delivered:** `game/ui/score_text.py` (changed, line 34).
3. **Checks** (from `game/`, `PYGAME_HIDE_SUPPORT_PROMPT=1`, `SDL_VIDEODRIVER=dummy`):
   - IS_CE assert passes. `py_compile` clean on `game/ui/score_text.py` and `game/ui/hud.py`.
   - `score_text` for 0, 999, 1000, 1234, 1000007, 1234567 prints `['SCORE 0', 'SCORE 999', 'SCORE 1 000', 'SCORE 1 234', 'SCORE 1 000 007', 'SCORE 1 234 567']`, unchanged from before the fix.
   - `game/tests/check.sh lint`: PASS lint, PASS format. `typecheck`: PASS.
   - `game/tests/check.sh ui`: 33 passed, 2 failed. Same two expected failures as in the first report (`test_hud_normal_layout_leaves_line_one_empty`, `test_hud_keeps_the_gap_below_the_overlay`), until task DRA-61-05. No test edited.
   - Grep of `game/ui/hud.py` and `game/ui/score_text.py` for the banned calls: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-61-02-ui-developer.md`.
7. **Status:** done.

### Decisions
- The return line is now `SCORE_LABEL + GROUP_SEPARATOR + GROUP_SEPARATOR.join(groups)`. The label gap and the group gap both come from `GROUP_SEPARATOR`, so no literal is left in the format.

### Answers
DRA-61-02-F1. Fixed: game/ui/score_text.py:34, the label-to-digits gap is built from `GROUP_SEPARATOR` instead of a literal space in the f-string.

## Fix 2026-10-18: docs/reports/qa/DRA-61-02-ui-developer.md

1. **Task:** Fix B1: this task built only `game/ui/score_text.py`, but `game/ui/hud.py` was also changed (task DRA-61-06's work). That broke two existing tests before task DRA-61-05 rewords them. Asked by QA.
2. **Delivered:** `game/ui/hud.py` restored to `HEAD` (`git checkout game/ui/hud.py`). `game/ui/score_text.py` unchanged. The removed hud.py diff is saved at `/tmp/claude-1000/-workspace/560f3b16-f48a-4957-8e50-a98c857bb711/scratchpad/hud_score_line.diff` for task 06 to reuse.
3. **Checks** (from `game/`, `PYGAME_HIDE_SUPPORT_PROMPT=1`, `SDL_VIDEODRIVER=dummy`):
   - Reproduced first: the diff of `game/ui/hud.py` against `HEAD` held only the SCORE-line change (19 insertions, 10 deletions).
   - `python -c "import pygame; assert pygame.IS_CE"` passes. `py_compile` clean on `game/ui/score_text.py`.
   - Acceptance command: `score_text` for 0, 999, 1000, 1234, 1000007, 1234567 prints `['SCORE 0', 'SCORE 999', 'SCORE 1 000', 'SCORE 1 234', 'SCORE 1 000 007', 'SCORE 1 234 567']`. pygame in `sys.modules`: `False`.
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS. ui: 35 passed. `QA: pass`. No test edited.
   - Grep of `game/ui/score_text.py` and `game/ui/hud.py` for the banned calls: no hits. Grep of `game/core/` for ui imports: no hits.
   - Draw run not repeated: `score_text.py` is pure and draws nothing, and `hud.py` is back to `HEAD`.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, bug report `docs/reports/qa/DRA-61-02-ui-developer.md`. Task DRA-61-06 re-applies the SCORE line in `hud.py` after DRA-61-05 lands.
7. **Status:** done.

### Decisions
- Restored with `git checkout`, as QA proposed: the whole `hud.py` diff was this task's out-of-scope change, so nothing else was lost.
- The earlier sections above describe the `hud.py` change as delivered. That is no longer true. This fix reverts it.
