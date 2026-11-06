Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-148-04 (Architect): the level-up banner on the play area. `LevelUpFonts`, `LevelUpView` with `__init__`, `draw_banner` and `bump_offset`. Task file: `docs/contracts/DRA-148/tasks/DRA-148-04-ui-developer.md`.
2. **Delivered:** `/workspace/game/ui/level_up_view.py` (new). No other file touched. `draw_flight` is left out (task DRA-148-06).
3. **Checks:** run from `/workspace/game`. Acceptance script (outside the repo): `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/accept.py`. Command: `PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/accept.py /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/shots`. It builds the look from the values of `tuning/level_up.json` (plain `json`, palette keys from `tuning/hud.json`, the records of `ui/level_up_rules.py`: these satisfy the schema), the real Exo 2 Bold (88) and Share Tech Mono (14) fonts, and a real `HudView` built from `load_hud_rules()` and `load_hud_art()`. `__init__` takes about 25 to 35 ms.
   - **Moments**, level 3, 640 x 480 field, PNGs in `.../scratchpad/shots/banner_<age>_<moment>.png` (a crop of the band area of all ten: `shots/sheet.png`; a 2x zoom of the number: `shots/zoom.png`). Numbers are measured on a plain field; "ink" is any pixel that is not the field, the glass or the hairline color.
     - age 6, opening: glass 78 rows (201 to 278), the hairlines shorter than the field width (none at the wall), no LEVEL, no pips; the number has not entered yet (`fall_start` 4, still above the area).
     - age 14, falling: full glass (rows 181 to 298), the two hairlines at rows 180 and 299 with corner ticks, the number falling through the band in the stretched pose; no ring or streaks yet, no LEVEL.
     - age 22, landing: full band, the number landed and squashed wide (276..364 x 196..280), the ring at its start size (48 px) and the 12 streaks at full strength around it; LEVEL not yet visible (fade starts at 22), no pips.
     - age 26, landing + 4: the number settling back toward 1x, the ring and streaks grown and fading (ink spans y 156..325), LEVEL faintly in, the first pip not yet in.
     - age 34, label and pips fading in: LEVEL half visible with letters still spread, ring and streaks almost gone, the first pips popped in (two lit, the third a small white flash); the rest not yet started.
     - age 48, pips in: LEVEL settled, all 8 pips in, 3 lit and 5 unlit, the new pip back to its lit color; ring and streaks gone; the glint has just started at the left of the number.
     - age 52, glint: same as 48, with the slanted glint across the middle of the number, lighting only the digit's own pixels.
     - age 80, hold: full band, LEVEL, 8 pips, the number at rest (293..346 x 196..274), nothing else.
     - age 100, flight start: the number is no longer drawn on the field (25 ink px left in the number zone); LEVEL and the pips are fading out (hold fade 96 to 106); the glass and hairlines still full.
     - age 124, closed: nothing drawn (0 glass rows, 0 ink px anywhere). The glass closes first (ages 100 to 115) and the lines after; the contact sheet shows the closed state.
   - **Stand-ins** (`shots/standins_080.png`): at age 80 a 40 x 50 "drifter" over the number and a 30 x 30 "ship" over the glass, both drawn after the banner: every pixel of both is exactly its own color (True, True). The banner draws only into `field` and nothing after it.
   - **Fuchsia**: the HUD palette's `ship_lines` (255, 0, 174). Max count of that color in any frame, levels 2 to 8, ages 0 to 149 (1050 frames): 0.
   - **Timing**, 200 draws at age 60 (full band height, label, pips and number at rest), `draw_banner` only, this container, two runs: glass at `band.alpha` 120: 0.144 and 0.125 ms per draw. At `band.alpha` 0: 0.069 and 0.055 ms per draw. The glass costs about 0.07 ms. Glass methods on the band's 640 x 120 rows, 200 blits each, two runs: **multiply fill + add fill (chosen)** 0.060 and 0.071 ms; surface-alpha blit of one opaque image 0.213 and 0.206 ms; per-pixel-alpha blit of one RGBA image 0.056 and 0.088 ms. The per-pixel blit ties with the fills here, but it needs one image of the band and a source area per height, and the fills are exact and need no image. The browser build has no SIMD blit, so the fills (a plain fill over only the band's rows) are the safer choice. The browser check measures the real cost.
   - **Surfaces after `__init__`**: 1000 draws across ages 0 to 159, levels 2 to 8, with `pygame` in the view's module replaced by a counting proxy and `sys.setprofile` counting builtin calls: 0 `pygame.Surface(...)`, 0 `pygame.transform.*` calls, and 0 calls of `render`, `copy`, `convert`, `convert_alpha`, `subsurface`, `smoothscale`, `scale`, `rotate`, `rotozoom`, `get_bounding_rect`. 100000 draws for None: no builtin call at all, 1.6 microseconds per draw under the profiler, the field byte-for-byte unchanged. `bump_offset(None)` is 0; ages 20 to 39 give `[0, 0, 0, 2, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 0 ...]` (the landing is age 22).
   - `python3 -c "import pygame; assert pygame.IS_CE"`: ok. `python3 -m py_compile game/ui/level_up_view.py`: clean. `ruff check ui` and `ruff format --check ui`: no findings; `mypy --strict ui/level_up_view.py`: no issues.
   - `game/tests/check.sh ui`: pass. **`game/tests/check.sh lint` and `typecheck` fail, in a file that is not mine:** `game/tests/core/test_run_level_up.py` (new, untracked, written by the QA task DRA-148-07 while I worked): 4 E501 long lines (lines 1, 251, 330, 355) and one mypy error (line 630: `Item "None" of "LevelUpBanner | None" has no attribute "age_ticks"`). With that file excluded, lint, format and typecheck are clean for everything else, including `ui/level_up_view.py`. I did not touch it.
   - Grep of `ui/level_up_view.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`, `import time`, `datetime`, `pygame.time`, `print(`: no hits. Grep of `game/core/` for `import game.ui`, `from game.ui`, `from ui`, `import ui`: no hits.
4. **Assumptions:**
   - The contract says "eased" for the glass and gives the glint only a start and an end. The glint tints the 1x number (the last pose) only. If `glint.start` is set before the squash has settled, the glint is skipped until the number is at 1x. With the starting values (glint 44 to 60, settled at 30) this never shows.
   - A hairline tick is at most half the glass height, so while the glass opens or closes the ticks never cross each other. Not in the contract.
   - The word LEVEL is drawn letter by letter with the spacing in px between glyph boxes, with no kerning. The pip pop-in grows a diamond from 1 px to `pips.size` over `pop_ticks`; the new pip's flash starts at the same tick it appears. The contract gives no shape for the pop-in.
   - Ring and streaks fade linearly over their states (alpha `1 - state/ticks`) and move linearly. The contract says "fading out" only.
   - The fall's distance is the resting center plus half the stretched number's height, so the number's bottom edge starts at the top of the play area. Computed once per level in `__init__`.
   - `hud` and `field_origin` are accepted and kept (the Interface names them) but only the flight, task DRA-148-06, reads them.
   - A banner level outside 2 to `LEVEL_COUNT` raises `KeyError` (core never makes one; no silent fallback).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-148/tasks/DRA-148-04-ui-developer.md`. Left alone: `game/ui/hud.py` (task 05; `_ink_tiles` and `Tiles` are imported from it, see Decisions), `draw_flight` (task 06), `game/app/` and the draw order (Integration Engineer), and the failing `tests/core/test_run_level_up.py` (QA owns it; the Director may want it fixed before the gate is read).
7. **Status:** done.

## Decisions
- **One file, builders at module level.** `level_up_view.py` holds the view class (draw only) and private builder functions that run in `__init__`. The class keeps tuples of ready images; each draw method does one job. A second module would have been cleaner for size, but the task names one file.
- **Draw order** is the contract's: glass, hairlines, ring, streaks, LEVEL, pips, number. The number comes last so it sits on its own ring and streaks. Source: view.md, Presentation.
- **Glass method:** multiply fill by `255 - alpha` then add fill of `glass * alpha / 255` on the band's rows, which is `dst x (1 - a) + glass x a`. The fills clip to the field. `band.alpha` 0 builds no fills and the glass is skipped. Chosen over the other two for exactness, no image per height, and the browser having no SIMD blit (measured above).
- **Hairlines and ticks** are rect fills (6 per frame). Both lines follow the glass height, so at height 0 they sit on one row, as the contract says. The line reaches `round(line_share x half width)` from the center.
- **Ring** is a set of ink tiles per state, alpha baked into the pixels, so a draw is a handful of blits and no `set_alpha`. It uses `_ink_tiles` from `ui/hud.py` (the HUD's sheen method, as the contract asks) rather than a copy. **Flag for the Director:** that function is private to `hud.py`. Making it public (or moving it to `ui/shapes.py`) is a rename in task 05's file, which I did not touch.
- **Streaks** are one small image per angle, with a surface alpha set per draw (allowed by the contract's Cost rules). Each image is about 20 x 20 px, not a whole-ring bounding box.
- **The number**: glyph cropped to its ink, outline made by stamping an outline-colored copy at every offset within `outline_width`, gradient made row by row and multiplied by the glyph's alpha. Poses are `pose_steps + 1` smoothscaled copies from the squash scale to 1x, plus one stretched fall pose. The pose is the one nearest to `pose_scales(age)` by distance in scale space, so the curve stays in `level_up_motion.py`. The falling pose is used directly before `fall_end`.
- **Glint frames** are the 1x number with a slanted stripe tinted toward `colors.glint` by `glint.strength`, built with blend flags: a copy of the number set to the glint color keeping its alpha, multiplied by a parallelogram mask, drawn over a copy of the number. The mask never reaches beyond the number's own alpha.
- **LEVEL** images are made at `spacing_steps + 1` spacings, from `spacing_wide` (index 0) to `spacing_normal`. The step is the fade-in's share times `spacing_steps`, rounded. Opacity is fade-in x (1 - hold fade-out), as a surface alpha.
- **Pips** are level-independent images by ticks since the pip appeared: lit, unlit, and the flash (white to lit over `flash_ticks`). Each pip's start is `pips.start + round(i x (end - pop_ticks - start) / (LEVEL_COUNT - 1))`, so the first starts at `pips.start` and the last is fully in at `pips.end`. The row fades out with LEVEL.
- **Bump:** `bump_offset` calls `ui.level_up_motion.bump_offset` with the banner's age. The scroll is the app's.
- **Numbers, colors, text:** every value is from `game/tuning/level_up.json` through `LevelUpLook`; the only constants in the module are `LABEL_WORD` (the word LEVEL, a fixed word per the contract rationale), `WHITE` (the tint base for glyph renders, not a look value) and `FULL_ALPHA` (255). No palette color is named in code. Source for the word: 10-ui.md, `hud_level`.
- **No state** is kept between draws. Setting a surface alpha on the view's own images is the only write, and it is made before each blit that uses it, so drawing the same state twice gives the same picture. Core and the banner are never changed.

## Review fix 2026-11-06: docs/reports/review/DRA-148-04-ui-developer.md

Fixed: DRA-148-04-F1, DRA-148-04-F3
Not fixable: DRA-148-04-F2 (the finding asks for no change; the private name lives in task 05's file)

1. **Task:** Review fix, round 1: the glint lit the digit's outline (F1, must-fix); the number's center was computed twice (F3, should-fix).
2. **Delivered:** `/workspace/game/ui/level_up_view.py` (changed). No other file touched.
3. **Checks:** run from `/workspace/game`.
   - IS_CE ok; py_compile clean; `ruff check ui` and `ruff format --check ui`: clean; `mypy --strict ui/level_up_view.py`: no issues; `bash tests/check.sh ui`: PASS (786 passed).
   - Acceptance script re-run (same command as the first report, scratchpad `accept.py`): every section prints as before (moments, stand-ins exact, 0 fuchsia, 0.117 ms per draw with glass, no surface or scale call after `__init__`).
   - Glint check (scratchpad `glint_check.py`, same setup): for levels 2 to 8, every glint frame compared to the unglinted number. Visible pixels (alpha above 0) changed outside the glyph's fill: 0 in all seven levels. Fill pixels changed: 1819 to 2921 per level. (Fully transparent pixels get a new hidden RGB from the blit; their alpha stays 0, so they draw nothing.)
   - Screenshots regenerated: `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/shots/banner_052_glint.png` and `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/shots/zoom.png` (via `accept.py` and `zoom.py`). The stripe sits inside the strokes of the 3; the dark outline and the gaps are untouched.
   - Grep of `ui/level_up_view.py` for the banned names: no hits. Grep of `game/core/` for `import game.ui`, `from game.ui`, `from ui`, `import ui`: no hits.
4. **Assumptions:** None new.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, on `docs/reports/review/DRA-148-04-ui-developer.md`. Left alone: `ui/hud.py` (F2), `draw_flight`, `tests/core/test_run_level_up.py`.
7. **Status:** done.

**Decisions**
- `_digit_image` now returns the digit and a second image, same size, white with the glyph's alpha placed at the outline offset (the fill only). `_glint_frame` builds its tint from that image, so the stripe's alpha is the fill's alpha and the outline cannot be lit. Still made once in `__init__`.
- `_build_number` takes the number's resting center row as an argument; `__init__` passes `self._number_center[1]`. The fall distance and the draw position now come from one sum.

**Answers**
- DRA-148-04-F1. Fixed: game/ui/level_up_view.py:354 and :424, the glint tint comes from the glyph's fill alpha, not the outlined canvas.
- DRA-148-04-F2. Not fixable: the finding asks for no change; making `_ink_tiles` public is a rename in task 05's file (`ui/hud.py`), a Director decision.
- DRA-148-04-F3. Fixed: game/ui/level_up_view.py:117 and :327, `_build_number` receives the center from `__init__`; the second copy of the sum is gone.

## Fix 2026-11-06: docs/reports/qa/DRA-148-04-ui-developer.md

1. **Task:** Fix B1 (QA): at fall ages 0 to 4 the level 7 number (odd stretched height, 73 px) had its last row on field row 0, not fully above the play area.
2. **Delivered:** `/workspace/game/ui/level_up_view.py` (changed, line 395 in `_build_number`). No other file touched.
3. **Checks:** run from `/workspace/game`; scratchpad S = `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad`.
   - Reproduced first: `PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 $S/qa04_l.py $S/qa04shots` gave `7 [15, 15, 15, 15, 15]`, other levels 0.
   - After the fix, same command: levels 2 to 8 all `[0, 0, 0, 0, 0]` (changed pixels in rows 0 to 169, ages 0 to 4).
   - `$S/accept.py $S/shots` re-run: stand-ins exact (True, True), fuchsia max 0 over levels 2 to 8, ages 0 to 149, 100000 None draws change nothing.
   - IS_CE ok; py_compile clean; `ruff check .` and `ruff format --check .` clean; `mypy --strict ui/level_up_view.py` no issues; `bash tests/check.sh ui`: PASS (786 passed), `QA: pass`.
   - Grep of `ui/level_up_view.py` for the banned names: no hits. Grep of `game/core/` for `import game.ui`, `from game.ui`, `from ui`, `import ui`: no hits.
4. **Assumptions:** None new.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on the bug report `docs/reports/qa/DRA-148-04-ui-developer.md`.
7. **Status:** done.

**Decisions**
- `drop_px` is now `center_y + (fall.get_height() + 1) // 2`: the half height rounded up, so the fall center is a whole number and `get_rect(center=...)` puts the image's bottom at row 0 for odd and even heights. Fall offset is 0 from `fall_end`, so the picture at rest is unchanged. The curve in `level_up_motion.py` is untouched. This is the fix QA proposed.
