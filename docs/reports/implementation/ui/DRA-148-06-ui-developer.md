Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-148-06 (Architect): `LevelUpView.draw_flight` and the flight's pre-rendered sizes, built in `__init__`. Task file: `docs/contracts/DRA-148/tasks/DRA-148-06-ui-developer.md`. Extra ask from the main session: the last flight image is sized `round(w * start_scale)` by `round(h * start_scale)`, the HUD's first pop frame rounding, and a contact sheet of ages 100 to 126 is saved.
2. **Delivered:** `/workspace/game/ui/level_up_view.py` (changed: `draw_flight`, `_Flight`, `_build_flight`, `_flight_frame`, `_mix_size`, the flight built in `__init__`). No other file touched.
3. **Checks:** run from `/workspace/game`. Acceptance script (outside the repo): `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/flight_check.py`. Command: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/flight_check.py /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/shots`. It uses `load_hud_rules()`, `load_hud_art()` and the game's fonts, builds the `HudView` with a look and the `LevelUpView`, and a look of its own made from the schema's start values (`tuning/level_up.json` values: there is no loader yet). Window 856 x 518, banner level 3, previous 2, arrival 124. Result: `ALL ASSERTS PASSED`.
   - Nothing drawn outside the flight: ages 0 to 99 and 124 to 150 (127 ages): 0 windows differ from the HUD alone (field with banner, then HUD with the banner, then `draw_flight`). `None`: equal. Ages 100 and 123 do draw.
   - Start tick (age 100): number at its resting place, ink center (336.5, 250) against the place (336, 250): 0.5 px.
   - Per age 100 to 123 (frame size; ink center error against `fly_position`; the frame's mean color distance to the tier color (255, 200, 0)): 47x68, 0.5 px, 111.0 at 100; 44x66, 0.4, 91.6 at 104; 40x63, 0.5, 75.0 at 107; 37x61, 0.7, 59.7 at 110; 33x58, 0.1, 44.2 at 112; 30x56, 0.7, 29.3 at 114; 26x53, 0.6, 14.4 at 117; 23x51, 0.4, 2.8 at 120 to 123. Largest position error 1.0 px. Sizes never grow; every pre-made state is smaller than the one before; color distance never rises. Arc: at age 112 the ink center is y 301 against the straight line's 320.9, so it bows up.
   - Last flight state (age 123): frame 23 x 51 = `round(16 * 1.45)` by `round(35 * 1.45)` = the HUD's pop frame 0 (23 x 51). Blit rect center (718, 383) = slot center (718, 383); ink center (718, 383). Same for levels 2 to 8: last size == `hud._pop_frames[level][0]` size == `round(slot.size * start_scale)`, end == `level_slot(level).center`. The last frame's pixels are the tier color within 2 of 255 per channel (253, 198, 0): the SDL alpha blit rounds.
   - Cost: building the look's view made 185 surfaces, 12 renders and 84 scales in `__init__` (banner and flight, all levels). 500 `draw_flight` calls across ages 100 to 123 and levels 2 to 8: 0 surfaces (`pygame.Surface` constructor counted), 0 text renders (font proxies), 0 `smoothscale`/`scale`/`rotate`/`rotozoom`/`scale_by` calls.
   - Contact sheet, ages 100 to 126, window-sized frames (HUD drawn), 3 columns at half size: `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/shots/flight_sheet.png`. Full-size frames: `.../shots/flight_100.png` to `flight_126.png`. A 4x crop of ages 100, 112, 123 and 124: `.../shots/flight_crops.png`.
   - `python3 -c "import pygame; assert pygame.IS_CE"`: ok. `python3 -m py_compile game/ui/level_up_view.py`: clean. `game/tests/check.sh lint`: pass. `game/tests/check.sh typecheck`: pass. `game/tests/check.sh ui`: pass.
   - Grep of `game/ui/level_up_view.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for `import ui` and `from ui`: no hits.
4. **Assumptions:**
   - "Shrinks on every state": there are `fly.steps` (8) sizes over 24 ticks, so the size changes at every pre-made state and holds for about 3 ticks between them. A strict shrink each tick would need a scale per frame, which the contract forbids. Say so if "state" meant each tick.
   - The progress is `fly_share(age, fly, banner.arrival_ticks - 1)`: the ramp ends on the last drawn age. With `arrival_ticks` itself the last drawn age (123) would be at share 0.995, 1.9 px short of the slot, past the 1 px the acceptance check allows. The hand-off to the pop then has no jump at all. Nothing else is changed in `level_up_motion.py`.
   - The pre-made image for a progress is the nearest: index `round(share * (steps - 1))`. Step `k` has progress `k / (steps - 1)` for both its size and its color mix.
   - Fit, not stretch. The HUD's `LevelSlot.size` is the font render's box (16 x 35, with line height), while the banner's number is cropped to its ink (47 x 68 with outline). Stretching to 23 x 51 would squash the digit; instead each image is exactly the interpolated size and the number is scaled evenly inside it, centered, on a transparent canvas. The image size and center are the slot's as the contract says; the visible ink is smaller than the image (23 x 33 at the last state).
   - The whole number, outline included, mixes to the tier color, so the last frame is a flat tier-colored digit. The HUD's own pop frame 0 is the flash white, not the tier color; that is task 05's design and is not touched.
   - The look in the script is mine (the schema's start values); the game's `level_up.json` has no loader yet.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-148/tasks/DRA-148-06-ui-developer.md`. Left alone: `game/ui/hud.py`, `level_up_motion.py`, `level_up_rules.py`, the draw order and the app's call (Integration Engineer), tests, `tuning/level_up.json`. The `arrival_ticks - 1` choice is the one spot a reviewer may want to confirm against the contract's "ends on the arrival tick".
7. **Status:** done.

## Decisions
- **`_Flight` record per level.** Holds the frames and the end point (`slot.center`), built once in `__init__` for levels `FIRST_LEVEL + 1` to `LEVEL_COUNT` (the same levels as `_numbers` and the HUD's pop frames). `draw_flight` never calls the HUD: it reads the record. The start point is the field origin plus the number's resting center, kept as `_flight_start`.
- **Frames come from `poses[-1]`**, the plain 1x number already built for the banner, so the flight's first image is the banner's last image: no jump at fly.start (the field stops drawing the number at the same age).
- **Tint by two fills.** `dst * (1 - share) + tier * share` is one multiply and one add on the RGB channels (alpha kept), done at build time on a copy. Same method as the glass.
- **One scale per frame image, in `_scaled`** (existing helper), then a blit onto a transparent canvas of the exact size. Step 0 is returned as it is: it has the resting size already.
- **Sizes** are `_mix_size` of the resting size and `round(slot.size * pop.start_scale)`. Both numbers come from `look.pop.start_scale` and the HUD's `level_slot`. The rounding is Python's `round`, the same call the HUD's pop frames use, so the sizes are equal (asserted for levels 2 to 8).
- **Early return for the age window** in `draw_flight` (`fly.start <= age < arrival_ticks`): outside it, and for None, the call returns at once.
- **Source of numbers.** `fly.start`, `fly.arc_px`, `fly.steps` and `pop.start_scale` are the tuning file's; colors are `LevelSlot.color`. No constant added.

## Review fix 2026-11-06: docs/reports/review/DRA-148-06-ui-developer.md

Fixed: DRA-148-06-F1

1. **Task:** Review fix, round 1: answer DRA-148-06-F1 (should-fix). F2 and F3 ask for no change.
2. **Delivered:** `/workspace/game/ui/level_up_view.py` (changed: `LevelUpView.__init__`).
3. **Checks:** run from `/workspace/game`. `python3 -c "import pygame; assert pygame.IS_CE"`: ok. `python3 -m py_compile ui/level_up_view.py`: clean. `tests/check.sh lint`, `typecheck`, `ui`: pass (786 passed). Acceptance script `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/flight_check.py` re-run: `ALL ASSERTS PASSED`, same results as the first run. Grep of the file for the forbidden calls: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, on `docs/reports/review/DRA-148-06-ui-developer.md`. F2 (contract wording of the arrival tick) is for the Architect; F3 (color and glyph change at hand-off) is for QA.
7. **Status:** done.

## Decisions
- Removed `self._hud` and `self._field_origin`; the constructor parameters stay, so the Interface is unchanged. Both are used only while building `_flight_start` and the `_Flight` records.

## Answers
- DRA-148-06-F1. Fixed: game/ui/level_up_view.py:123-125 and 128, dropped the two unused attributes and corrected the `__init__` docstring sentence.

## Fix 2026-11-06: docs/reports/qa/DRA-148-06-ui-developer.md

1. **Task:** Fix mode, bug B1: the flight's last image put the digit's ink in the middle of the image, the HUD's first pop frame puts it lower, so the digit dropped 2.5 to 3.5 px on the arrival tick. Only `game/ui/level_up_view.py` edited; `hud.py` untouched (under QA re-test).
2. **Delivered:** `/workspace/game/ui/level_up_view.py` (changed: `LevelUpView.__init__` passes the pop ink rect, `_build_flight` takes `pop_ink`, new `_mix_rect`, `_flight_frame` places the digit by ink rect).
3. **Checks:** run from `/workspace/game`. Scratch scripts (outside the repo): `.../scratchpad/qa06e.py` (QA's repro), `.../scratchpad/fix06.py`, both with the arg `.../scratchpad/qa06shots`. Reproduced first: QA's numbers. After the fix, ink rects in the image, flight last frame against pop frame 0 (levels 2 to 8): level 2 `(1,12,22,31)` vs `(1,11,22,33)`; 3 `(2,13,21,31)` vs `(1,13,22,31)`; 4, 5, 6 identical; 7 `(1,13,22,30)` vs `(1,13,22,31)`; 8 `(3,13,23,31)` vs `(2,13,25,31)`. Ink centers in the window at age 123 against the pop's first frame: equal at every level (e.g. level 3 (719, 386) both; before the fix 3 px apart). Ink size is within 2 px wide and 2 px tall (level 2: 31 vs 33 tall; level 8: 23 vs 25 wide). Image size and the blit center are unchanged (same size as pop frame 0, center = slot center). `python3 -c "import pygame; assert pygame.IS_CE"`: ok. `ruff check .` and `ruff format --check .`: clean. `py_compile`: clean. `bash tests/check.sh`: 786 passed, `QA: pass`. Grep of the file for the forbidden calls: no hits; grep of `core/` for ui imports: no hits. No new per-frame work: the ink rects and fitted images are made in `__init__`; `draw_flight` is unchanged.
4. **Assumptions:** The digit is fitted evenly (not stretched) into the interpolated ink rect, so one side matches exactly and the other can be 1 to 2 px short (the pop's digit has no outline and a different aspect). Stretching would warp the number during the flight.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on `docs/reports/qa/DRA-148-06-ui-developer.md`. Note for QA: the first run's acceptance script (`flight_check.py`) and the task's "ink center within 1 px of the slot center" now differ by design. The image box center is on the slot center (and the path) at every age; the visible digit's center at age 123 is where the pop draws it, 3 px below the slot center, because the HUD's number image has empty rows above its ink. Matching the pop's ink (B1) and putting the ink on the slot center cannot both hold. I followed B1. If QA wants the other, the contract wording needs the Architect.
7. **Status:** done.

## Decisions
- **Chose `hud._pop_frames[level][0].get_bounding_rect()`, read once in `__init__`**, not a public `HudView` method. `level_slot` gives center, image size and color only, no ink position, and `hud.py` could not be changed. Only the resulting `pygame.Rect` is kept (in the flight images); no reference to the HUD or its surface is stored. The module already imports `_ink_tiles` from `ui.hud`, so this is the same coupling. A public `HudView.level_slot` field for the ink rect would be cleaner; that is a `hud.py` change for a later task.
- **Ink rect moves by `share`.** At step k the target ink rect is `_mix_rect(resting ink, pop ink, k / (steps - 1))`: step 0 is the resting number whole, the last step is the pop frame's ink rect. Size and position change together, so no step jumps.
- **Scale from the ink rect, not the whole image.** `_flight_frame` crops to the resting ink rect, scales evenly by `min(ink.w / w, ink.h / h)` and centers on the target ink rect.
- **`_flight_frame` takes `tint: tuple[RGB, float]`** (tier color, share) to keep the parameter list at five.
