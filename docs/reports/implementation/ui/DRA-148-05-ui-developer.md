Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-148-05 (Architect): the HUD's level pop. `LevelSlot`, the optional look and banner arguments, the shown level, the pop (number, new climb bar, box outline) and `level_slot`. Task file: `docs/contracts/DRA-148/tasks/DRA-148-05-ui-developer.md`.
2. **Delivered:** `/workspace/game/ui/hud.py` (changed). No other file touched.
3. **Checks:** run from `/workspace/game`. Acceptance script (outside the repo): `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/pop_check.py`. Command: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/pop_check.py`. It uses the game's `load_hud_rules()` and `load_hud_art()`, the committed `hud.py` (copied before the edit) as the old construction, and a look of its own (pop: 20 ticks, start 1.5, undershoot 0.9 at 0.5, flash 10, 10 steps, bar flash 12, box flash 14 ticks at 2 px, corner cut 8). Result: `ALL ASSERTS PASSED`.
   - Pixel equality: 24/24 whole-window draws equal the old HUD (levels 1 to 8; old construction vs new construction with no arguments, the same with a banner but no look, and a look but no banner).
   - The pop, previous level 2, level 3, banner arrival 120, level box crop (4x, side by side): `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/shots/pop_sheet.png` (ages 119, 120, 121, 125, 130, 139, 140; one PNG per age beside it). Age 119: crop is byte-equal to a plain level-2 HUD (number 2, 2 bars). Age 140: byte-equal to a plain level-3 HUD. Number size (normal 16 x 35): age 120 and 121 24 x 52 (x1.50), 125 21 x 45 (x1.31), 130 15 x 32 (x0.94, the undershoot), 139 16 x 35 (x1.00). New bar color: age 119 dim (41, 52, 106); 120 (255, 255, 255); 121 (255, 249, 235); 125 (255, 225, 156); 130 (255, 194, 57); 139 and 140 lit color (255, 182, 17). Box top-edge pixel: baked (157, 6, 121) at 119, flash (255, 220, 60) at 120, fading through (220, 143, 82) at 125 and (185, 67, 103) at 130, baked again at 139.
   - `level_slot(level)` for levels 1 to 8: center inside the level box (inset 4 px), size equals `art.fonts["level"].size(str(level))`.
   - Surface count: building with a look made 5 surfaces, 117 text renders and 71 scales in `__init__` (the pop frames, the box outline and the level numbers); the HUD's own first draw renders the BEST and graze text (2 renders, as before this task). After that, 500 draws across ages 100 to 159: 0 surfaces (`pygame.Surface` constructor counted), 0 text renders (font proxies), 0 `smoothscale`/`scale`/`rotate`/`rotozoom` calls.
   - `python3 -c "import pygame; assert pygame.IS_CE"`: ok. `python3 -m py_compile game/ui/hud.py`: clean.
   - `game/tests/check.sh lint`: pass (ruff check, ruff format). `game/tests/check.sh typecheck`: pass (mypy strict, 148 files). `game/tests/check.sh ui`: 786 passed, the existing HUD tests unchanged.
   - Grep of `game/ui/hud.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for `import ui` and `from ui`: no hits.
4. **Assumptions:**
   - The pop's number frame `k` is the pop at tick `round(k * pop.ticks / (steps - 1))`, so frame 0 is exactly the arrival size and the last frame is the normal image. The frame shown at tick `e` is `round(e * (steps - 1) / pop.ticks)`. The contract says "a pre-rendered frame per step" and nothing more.
   - The arrival frame's size is `round(width * pop.start_scale)` by `round(height * pop.start_scale)` (`smoothscale`). Task DRA-148-06's flight must use the same rounding for its last size to be this image.
   - The box outline's flash is a polygon outline (`pygame.draw.polygon`, `box_flash_width` thick, the corners cut top-right and bottom-left as the art tool draws them), drawn inward from the box's edge pixels. It covers the baked edge and `box_flash_width - 1` px inside it. The art tool's cut corners are `10 x panel.scale`; the value used is the look's `pop.box_corner_cut`, as the schema says.
   - The pop's number and bar use `banner.level`; the rest of the readout uses `shown_level(banner, run.level)`. In play they are the same value.
   - The look's own colors and numbers in the acceptance script are mine; the game's `level_up.json` has no loader yet (`game/app/level_up_tuning.py` is not in this task).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-148/tasks/DRA-148-05-ui-developer.md`. Left alone: `hud.json`, `tools/art/hud_panel.py`, the panel art, `game/app/`, the banner view and flight (tasks -04 and -06), tests. `git status` also shows `game/core/run.py` and `game/core/waves.py` modified and `game/core/level_up.py` new: the Gameplay Implementer's tasks, not mine.
7. **Status:** done.

## Decisions
- **One optional look, kept as `_look`.** `HudView.__init__(rules, art, level_up_look=None)`. With None, `_pop_frames` and `_box_flash` stay empty and `draw` ignores `level_up`; that is what keeps the old HUD pixel-equal, including when a banner is passed without a look (the contract: "no look given: exactly the old HUD, with `run.level`").
- **`_Pop` record.** `_active_pop(banner)` turns the banner's age into one small frozen record (level, frame index, flash color, bar share, box opacity), once per draw. `_draw_level` and its helpers then only read it. The pop reads `banner.age_ticks - banner.arrival_ticks`, never the view `tick`, so it freezes with the run. Source: level-up/view.md, Presentation; hud.md, Rules.
- **Fades.** The number's flash, the new bar's flash and the box flash all use `level_up_motion.fade_share(elapsed, 0, <ticks>)`; the number's size uses `pop_scale`. No curve is written in `hud.py`.
- **Draw order in the level box.** Box flash, number, bars. The flash is over the baked outline (it is in the panel blit) and under the number, so a large arrival number is not cut by it.
- **Thin outline as small images.** The flash outline is drawn once on a transparent surface and cut into `INK_TILE` (16 px) cells, each trimmed to its ink (`_ink_tiles`, the method of `_sheen_slices`). Per frame: a `set_alpha` and a blit per cell (about 16), never one picture of the whole box. `INK_TILE` is an implementation constant, not a tuning value.
- **Level numbers rendered in `__init__` when a look is given.** `_build_pop` fills the per-level number cache for levels 1 to 8, so the rise tick and every pop frame render no text (the HUD used to render a level's number on its first draw). With no look nothing changes: the cache still fills lazily.
- **`_tier_color` and `_number_rect` extracted** from `_draw_level` and `_level_number`, because `level_slot`, the pop frames and the old draw all need them. The old path blits the same image at the same rect with the same bar colors: the 24 pixel-equality draws prove it.
- **`level_slot` fills the number cache** on a first call for a level (a lazy render, the same one the HUD's draw would make). It draws nothing and changes no visible state. The level view calls it in its `__init__`.
- **Numbers and colors.** Every pop value is `PopLook` (tuning `pop` section); `flash` and `box_flash` are `look.colors`; tier colors come from the HUD rules as before. The only constant I added is `INK_TILE`.

## Fix 2026-11-06: docs/reports/qa/DRA-148-05-ui-developer.md

1. **Task:** Fix B1 (QA): the box flash's two cut corners did not line up with the baked outline.
2. **Delivered:** `/workspace/game/ui/hud.py` (`_box_outline`, the polygon corner list). No other file touched.
3. **Checks:** run from `/workspace/game`.
   - Reproduced first with QA's script: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa05/edge.py`. Before the fix: 7 baked pixels uncovered outside the number's rectangle (4 top-right, 3 bottom-left).
   - After the fix, same script, part 7: uncovered baked pixels outside the number's rectangle: 2, `(705, 396)` and `(706, 397)`. Part 6: top-right uncovered 0. Part 2: flash pixels on interior-colored pixels 0 (the flash draws nothing off the baked outline).
   - The 2 left are faint antialiased pixels of the baked bottom-left diagonal, which is two pixels wide; width-1 flash cannot cover them (QA measured the same with the proposed corners). Not further fixable without changing `pop.box_flash_width` (the Director's tuning) or the art.
   - `python3 -c "import pygame; assert pygame.IS_CE"`: ok. `py_compile game/ui/hud.py`: clean. `ruff check game` and `ruff format --check game`: clean. `game/tests/check.sh lint`, `typecheck`, `ui`: PASS.
   - Grep of `game/ui/hud.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for `game.ui` and `ui` imports: no hits.
4. **Assumptions:** The 2 remaining faint pixels are acceptable at flash width 1 (the shipped width); the contract says the flash is drawn over the baked outline, not that it hides every antialiased pixel.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, Verify mode, on `docs/reports/qa/DRA-148-05-ui-developer.md` (B1). QA's note about the flight ending in the tier color against the pop's white first frame is for the Architect; left alone.
7. **Status:** done.

## Decisions
- Took QA's proposed corners. Both diagonals now run `cut - 1` px in x and y, so they are 45 degrees and land on the baked pixels: top-right end `(pad + width - 1, pad + cut - 1)`, bottom edge start `(pad + cut - 1, pad + height - 1)`, left edge end `(pad, pad + height - cut)`. The cut size is still `pop.box_corner_cut`.
- Nothing else changed: draw order, tiles, frame counts and the old-HUD equality path are untouched, so those earlier numbers stand (the UI suite still passes).
