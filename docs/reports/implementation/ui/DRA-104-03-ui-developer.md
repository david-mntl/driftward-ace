Status: ready-for-review
Created by: ui-developer

1. **Task:** build the UFO view and register it, `docs/contracts/DRA-104/tasks/DRA-104-03-ui-developer.md`, from the Architect.
2. **Delivered:**
   - `game/ui/drifters/ufo_view.py` (new): `UFO_DISC_COLOR`, `UFO_DOME_COLOR`, `render_ufo` registered for `DrifterType.UFO`.
   - `game/ui/drifters/__init__.py` (changed): one import line for `ufo_view`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `py_compile` on both files: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 83 files formatted. `game/tests/check.sh lint`: pass.
   - `check.sh typecheck`: pass (79 files, no issues). `check.sh ui`: 46 passed.
   - `check.sh core`: fails at collection, `tests/core/test_collision.py:1753 KeyError: 'hitbox'`. This is the failure the drifters contract's DRA-104 Impact table lists for that file (`load_variant_cases` reads `raw["hitbox"]` from `ufo.json`; QA task DRA-104-04). Not caused by this task.
   - Acceptance command (from `game/`, the exact command in the task, run via a scratch copy of it), output:
     ```
     (170, 170, 185) (170, 170, 185) (170, 170, 185)
     (90, 220, 110) (90, 220, 110)
     (0, 0, 0) (0, 0, 0) (0, 0, 0) (0, 0, 0)
     (128, 128, 139) (68, 165, 83)
     (170, 170, 185) True True
     ```
     All five lines match the task.
   - Follows the state: `replace(ufo, y=250.0)` drawn on a fresh surface: (320, 300) is background and (320, 250) is the disc grey. `repr(ufo)` is identical before and after drawing. Two draws of one state give identical bytes. A UFO whose hitbox is only the disc raises `TypeError: render_ufo draws a box then a circle, disc then dome`.
   - Grep of the two files for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `game.ui` and `ui` imports: no hits.
4. **Assumptions:** None beyond the contract. The view reads `drifter.hitbox` as disc then dome, as `ufo_hitbox` builds it.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-104/tasks/DRA-104-03-ui-developer.md`. The QA tasks DRA-104-04 to 06 own the `check.sh core` failure above. I left `ui/drifters/registry.py`, `entry_warning.py`, `ui/shapes.py` and the debug overlay alone, as the task says.
7. **Status:** done.

## Decisions
- Draw order: dome first, then disc on top, so the dome's lower half sits under the disc. Source: contract, Presentation, UFO.
- Both shapes go through `draw_shape` with offsets and sizes times `scale`, so the full-size look sits on the debug outlines. No scaling math beyond that.
- Colors (170, 170, 185) and (90, 220, 110) are constants in the view, with the dimming through `dim_color`. Source: contract Interface and 07-ufo.md placeholder_look (guess). No tuning key exists for them; the contract keeps colors in views.
- The hitbox check mirrors the satellite and fireball views (`_disc_and_dome`), with the contract's error text.
- The warning copy needs no code: `draw_entry_warning` calls this view at scale 0.35 with `warning_copy()`.
