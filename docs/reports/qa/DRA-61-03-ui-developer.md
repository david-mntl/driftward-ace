Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-61-03-ui-developer (three-line layout and `draw_final_score` in `game/ui/game_over.py`), Verify mode, asked by `/implement`.
2. **Delivered:** docs/reports/qa/DRA-61-03-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: all steps PASS, ends `QA: pass` (35 ui tests).
   - Acceptance check from the task, run unchanged (from `game/`, dummy video, `PYTHONPATH=game`): prints `2 3 3`, `True`, `True`, `True`.
   - Pixel check against an independent layout worked out from the fonts (title font 32, score and prompt font 16, `get_linesize()` / `get_height()`, box at (160, 180)): `draw_game_over` alone matches pixel for pixel; `draw_final_score(s, 1234)` matches a reference render of `score_text(1234)` centered at title top + title line-height. Both True.
   - Title and prompt rows are the same with and without the score line, on 640x480, 800x600, 321x121, 320x120 and 1000x300 surfaces. Score-only draw touches nothing but its text (box corner pixel unchanged).
   - Score text: `0`, `7`, `1234`, `1234567` give `SCORE 0`, `SCORE 7`, `SCORE 1 234`, `SCORE 1 234 567`.
   - Two game overs in a row, scores 10, 99999, 10: pixels differ for the first two and are identical for the first and third. The one-entry cache renders again.
   - Build once: scores 5,5,5,6,6,5 give hits=3, misses=3, maxsize 1.
   - Long scores: `10**20` (33 chars, 197 px) is centered inside the box. `10**40` (346 px) and `10**200` (1534 px) stay centered and run past the box sides. The contract allows this: no digit limit, centered however long, unreachable in play (run.md, Width and Rationale).
   - Same inputs twice: identical frames.
   - `game/app/frame.py` still makes only the `draw_game_over` call, so the box shows no score yet. That call is the Integration Engineer's (task, Out of scope).
   - Review notes: F1 is a note on the Decisions text only, no code change. Each **For QA** line was run, except the HUD font match, which waits for DRA-61-06.
   - 0 bugs.
4. **Assumptions:** After `pygame.quit()` then `pygame.init()`, `draw_final_score` raises `pygame.error: Invalid font` because the cached score font is dead. I did not file it. The contract says the fonts are built once and gives no promise about a font restart. `hud.py` and `debug_overlay.py` cache fonts the same way, the app never quits pygame, and no test calls `pygame.quit()`. The DRA-61-05 test task should keep the session `pygame_headless` fixture and never quit pygame.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, add the `draw_final_score(surface, run.score)` call in `game/app/frame.py`, per `docs/contracts/systems/app.md`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
