Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-23-02-ui-developer.md` (UI Developer, task `docs/contracts/DRA-23/tasks/DRA-23-02-ui-developer.md`) against `docs/contracts/systems/hud.md`, Interface and Presentation. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-23-02-ui-developer.md` (this file). Reviewed: `game/ui/hud.py`.
3. **Checks:** by reading only. Nothing run.
   - `draw_hud(surface: pygame.Surface, run: Run, below_overlay: bool) -> None` (`hud.py:59`) matches hud.md, Interface. The six DRA-13 constants (`:18-40`) and four heart constants (`:42-56`) match in name, type and value.
   - Heart slot math (`:82-84`): `first_left = width - 8 - 24`, step `24 + 8`, loop `range(lives)`. On 640 px that gives x 608, 576, 544, row 8. Matches hud.md, Presentation, slot formula and the three positions.
   - Heart shape (`:95-109`): circles r 6 at (6, 6) and (17, 6), polygon (0, 7), (23, 7), (12, 23), (11, 23). It is symmetric about x 11.5, reaches columns 0 and 23 through the polygon's top edge and row 23 through its point, and stays inside 0 to 23. Matches hud.md, Presentation, Hearts. The saved image `hud_debug.png` (implementation report, Checks) shows a readable heart at the top right.
   - The scratchpad acceptance script `accept.py` matches what the report describes: two 640 x 480 surfaces filled with `ui.look.BACKGROUND`, the two `Run`s from the task, the slot-box check and the bbox over x 600 to 639, rows 0 to 39. The printed bbox (x 608 to 631, y 8 to 31) is what the geometry above predicts.
   - Test claim: `tests/ui/test_hud.py` has exactly 5 tests and each passes a `Scroll` to `draw_hud` (`test_hud.py:65`, `:124`), so `run.scroll` raises `AttributeError: 'Scroll' object has no attribute 'scroll'` as reported. `test_error_screen.py` has 3 tests. 5 failed, 3 passed is consistent.
   - Imports (`:8-14`): `logging`, `functools.cache`, `pygame`, `core.run.Run`, `ui.debug_overlay.overlay_text_bottom`. No `core.scroll`, no `app`. No fill, flip, log call, `try`, key or mode read.
   - Lint pass is plausible: imports sorted by section, every function annotated, longest line about 93 characters (limit 100).
   - 0 must-fix, 0 should-fix, 3 notes.
4. **Assumptions:** I took the readout's text, place, font and color as unchanged by comparing `hud.py:67-71` with hud.md, Presentation. I didn't diff against the previous version.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: run the checks for `docs/reports/implementation/ui/DRA-23-02-ui-developer.md`. Must-fix count: 0. The 5 `test_hud.py` failures are expected until DRA-23-05. Until the Integration Engineer updates `game/app/frame.py`, a smoke run of the game fails on the first frame (note 1).
7. **Status:** done.

## Findings
1. **note** `game/app/frame.py:143`: the app still calls `draw_hud(surface, scroll, below_overlay=debug)`. With this task's signature, the first HUD draw raises `AttributeError`, so the running game breaks until the app passes `run`. This is outside the task's lane. hud.md, Impact gives it to the Integration Engineer, and the implementation report says so in Next. Rule: the contract's Impact table. Source: `docs/contracts/systems/hud.md`, Impact. Change: none in this task. The Integration Engineer passes `run`, per `docs/contracts/systems/app.md`.
2. **note** `game/ui/hud.py:96-98`, `:107`: the heart geometry uses the ratio `HEART_SIZE // 4` and two `+1`/`-1` offsets. The contract fixes only the look and the extent, and the implementer declares the geometry under Assumptions, so these values aren't hidden. With an odd `HEART_SIZE`, the 2-px point at (`middle`, `middle - 1`) would sit half a pixel off center. That doesn't matter at 24. Rule: no magic numbers. Source: game/CONTEXT.md, Good practice; checklist item 8. Change: none needed for a temporary stand-in waiting on UI-02. If the shape stays, name the lobe ratio.
3. **note** `game/ui/hud.py:16`: `log` is defined and never used. game/CONTEXT.md, Logging requires it for a module with code, and hud.md, Presentation forbids logging per frame. Rule: module logger. Source: game/CONTEXT.md, Logging. Change: none.

## Checklist
1. Interface matches exactly: **pass**. `draw_hud` (`:59`) and all ten constants match hud.md, Interface. `_draw_hearts` and `_heart` are private helpers.
2. UI/core split: **pass**. The heart count is `run.lives` as read (`:72`), and the readout is `run.scroll.meters` (`:70`). No life math, no rule, no timer. The run is not mutated (frozen dataclass, and the acceptance script compares `repr` before and after). `game/core/` doesn't import `ui`.
3. Fixed 60 Hz tick: **n/a**. No timing in the view.
4. Randomness only from a passed-in `random.Random`: **n/a**. No randomness.
5. Browser rules: **pass**. No sleep, thread, `await`, file load, image file or audio. No path used.
6. Every number traces to its source: **pass**. The heart constants trace to scope report DRA-23, Values needed (24 x 24, 8 px apart, 8 px from the top and right edges, white), and their docstrings say temporary stand-in, not in the GDD, UI-01 and UI-02 TBD, as the task requires. 10-ui.md, `lives_display` is TBD and was not filled in. Shape ratios: note 2.
7. Pillars and locked decisions: **pass**. Lives show at the top right (10-ui.md, `hud_lives`, locked). Three hearts match `lives_start` 3 through `run.lives`. No movement, wall or hazard touched.
8. Smells: **pass**. Three short functions, no nesting beyond one loop, no duplication, no dead or commented-out code, type hints on every function and local. The `@cache` on `_heart()` holds one drawn surface, not game state. It is the same pattern as `_hud_font()`, and hud.md, Presentation asks for build once and keep. Notes 2 and 3.
9. Decisions present and matching the code: **pass**. Five Decisions, each matching: `@cache` on `_heart()` (`:87`); `_draw_hearts` separate, slot 0 rightmost, `range(lives)`, width from `surface.get_width()` (`:75-84`); hearts ignore `below_overlay` (`:72`); constant docstrings from the task (`:43-56`); module docstring updated (`:1-6`).
10. Report claims match the files: **pass**. Delivered, the import change, the grep claims, the acceptance script and the expected test result all match what I read.

## For QA
- Draw with `lives` 3, 2, 1, 0. Filled slots go right to left from x 608, slot 0 never moves, and 0 draws no heart.
- On a surface that isn't 640 px wide (for example 800), slot 0's box is at x `width - 32`, row 8.
- Hearts are pixel-identical with `below_overlay` True and False, and every heart pixel lies inside its 24 x 24 box, touching columns 0 and 23 and row 23.
- `_heart()` returns the same surface object across draws (built once, never per frame).
- Readout tests in DRA-23-05 must count only white pixels left of the hearts, because the hearts are white too (hud.md, Impact).
