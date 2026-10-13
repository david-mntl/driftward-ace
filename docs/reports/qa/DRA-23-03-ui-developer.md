Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-23-03-ui-developer (Game Over box, `game/ui/game_over.py`), Verify mode, started by the Director's session. Scope: task 03 only, as instructed.
2. **Delivered:** docs/reports/qa/DRA-23-03-ui-developer.md. Inline scripts and images stayed in the scratchpad (`qa_go.py`, `qa_1.png`, `qa_2.png`); nothing saved in `game/tests/`.
3. **Checks:**
   - `game/tests/check.sh`: env PASS, lint PASS, format PASS, core FAIL, ui FAIL. All 7 failures are outside task 03, see Harness. `check.sh lint` alone ends `QA: pass`.
   - Acceptance check reproduced from `game/` (headless, `ui.look.BACKGROUND`, `draw_starfield(Scroll(ticks=130, scrolled_ticks=100))`, then `draw_game_over`; then a (90, 100, 140) fill):
     ```
     inside (165,185): (58, 64, 90)   outside (100,100): (90, 100, 140)
     white bbox: x 251..387, rows 225..254   (inside x 160..479, rows 180..299)
     ```
     (58, 64, 90) is the contract's "about (58, 65, 91)": 165/255 of (90, 100, 140) rounds down. Image 1 shows stars, a faint box, white "Game Over" with the smaller "Press any arrow to retry" under it, both centered on x 320.
   - Edges on 640x480: box corner (160,180) and (479,299) are darkened; (159,180), (480,299), (479,300) are unchanged. So the box covers exactly 320 x 120 from (160,180).
   - Text layout: title line-size 24, prompt height 12, block 35, `title_top` = 180 + (120 - 35) // 2 = 222, as the contract's formula says.
   - Other surface sizes (800x600, 641x481, 320x120, 400x200, 1000x300): box top-left is ((w-320)//2, (h-120)//2) each time, both texts stay inside the box, and the text center is within 1 px of `w // 2`. 641x481 gives corner (160,180), as floor division says. A surface smaller than the box (200x100) draws without error. A SRCALPHA target also blends correctly.
   - Target surface is never filled: a (1,2,3) fill stays (1,2,3) at (0,0) and (639,479).
   - Build once: after two draws `_parts()` is the same object. The cached box keeps `SRCALPHA`, size (320,120) and pixel (0,0,0,90) after drawing, so drawing doesn't change it.
   - Determinism: two draws on equal surfaces give identical bytes.
   - Review "For QA": all five lines checked above. Drawing before `pygame.font.init()` raises `pygame.error` and is not caught.
   - Greps on `game/ui/game_over.py` for sleep, thread, asyncio, display, event, key, image.load, mixer, random, print, and `core`/`app` imports: no hits.
   - Review findings: 0 must-fix. Its 3 notes (report wording on cached fonts, docstring literals 320 and 120, unused `log`) change no behavior and are not bugs.
4. **Assumptions:** Verdict is scoped to task 03, per the instruction that the failing tests belong to other tasks. I did not re-run on a clean checkout of task 03 alone; I judged each failure by its cause (below).
5. **Documentation differences:** None.
6. **Next:** Integration Engineer for the task 03 piece (`draw_game_over` is ready for `game/app/frame.py`). The Director should note that `check.sh` is not `QA: pass` overall: `core/test_ship.py` is waiting on DRA-23-04, and `ui/test_hud.py` is waiting on DRA-23-02 (it must be fixed to the new `draw_hud` signature there). Neither is a bug in `game_over.py`.
7. **Status:** done.

## Bugs
None open for task 03.

## Harness
env PASS · lint PASS · format PASS · core FAIL · ui FAIL
QA: fail (core ui)

- core: `tests/core/test_ship.py::test_floor_respawns_at_spawn` and `::test_events_log_once` fail. This is the DRA-6 respawn stand-in that `game/core/ship.py` no longer does (modified in the tree by DRA-23-01). Expected until DRA-23-04.
- ui: five failures in `tests/ui/test_hud.py` (`test_hud_normal_layout_leaves_line_one_empty`, `test_hud_never_overlaps_the_debug_overlay`, `test_hud_keeps_the_gap_below_the_overlay`, `test_hud_does_not_jump_when_the_overlay_is_hidden`, `test_hud_stays_above_the_top_line`). `draw_hud` in `game/ui/hud.py` now takes a `Run` (`run.scroll.meters`), and the tests pass a `Scroll`. That is task 02's change. No test touches `game/ui/game_over.py`.
- `check.sh lint` alone: PASS lint, PASS format, `QA: pass`.
