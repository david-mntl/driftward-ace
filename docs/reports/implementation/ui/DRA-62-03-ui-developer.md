Status: ready-for-review
Created by: ui-developer

1. **Task:** build the coin's view (`render_coin`) and register it, from `docs/contracts/DRA-62/tasks/DRA-62-03-ui-developer.md` (Architect).
2. **Delivered:**
   - `game/ui/drifters/coin_view.py` (new): the four colors, `COIN_LINE_WIDTH`, `render_coin`.
   - `game/ui/drifters/__init__.py`: one import line for `coin_view`.
3. **Checks:** run from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile ui/drifters/coin_view.py ui/drifters/__init__.py`: clean.
   - `tests/check.sh lint` (ruff check + format): pass. `tests/check.sh typecheck` (mypy strict): pass, 61 files.
   - Acceptance command (the one in the task, `SDL_VIDEODRIVER=dummy python -c "..."`), output:
     ```
     (437, 203) (255, 220, 240)
     (436, 210) (200, 30, 90)
     (442, 210) (70, 0, 60)
     (434, 209) (255, 80, 150)
     (445, 209) (255, 80, 150)
     429 450 200 219
     ```
     This is the glint, lit side, shade side, rim twice, then the ink bounds the task expects.
   - Follows the state (inline run): coin moved 20 px down in y, ink moved exactly 20 rows, same pixel count. Common coin (glint False): (437, 203) is lit (200, 30, 90), no glint. Brightness 0.75: lit side (150, 23, 68), equal to `dim_color`. Fractional centers (440.4, 210.4), (440.6, 210.6), (100.5, 100.5): every pixel inside columns cx-11..cx+10 and rows cy-10..cy+9. Same state drawn twice: identical bytes. `repr(coin)` identical before and after the draw. `scale` 0.5 raises `ValueError("render_coin draws at full size only")`; a Meteorite raises `TypeError("render_coin draws a Coin")`.
   - Grep of `game/ui/` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `game.ui` / `ui` imports: no hits.
   - `tests/check.sh ui`: 45 pass, 1 fail: `test_drifter_registry.py::test_drifter_lists_match_everywhere`, because `game/tuning/drifters/coin.json` does not exist yet. The task says this test passes once that file exists. The coin view itself is registered (no "no view registered" error).
   - No screenshot saved.
4. **Assumptions:** none. The view uses the contract's polygon, ellipse and rect steps as written; the pixel map came out as stated.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-62/tasks/DRA-62-03-ui-developer.md`. `game/tuning/drifters/coin.json` is content owned by whoever the Director names; `test_drifter_registry.py` stays red until it exists. Left alone: the popup view (task DRA-62-04), `registry.py`, `entry_warning.py`, the other views.
7. **Status:** done.

## Decisions
- One function per draw step (`_draw_sides`, `_draw_rim`, `_draw_ring`, `_draw_glint`), called in the contract's order. The three half-size values travel as one tuple so each helper stays under five parameters.
- The rim corners and the side polygons are written from `half_width`, `half_height`, `half_body`, as the contract says, not as literals. They reduce to its full-size numbers at 12 × 20 / body 10.
- The view reads `drifter` through `isinstance(drifter, Coin)`, which also narrows the type for mypy. It copies nothing and writes nothing.
- Colors and `COIN_LINE_WIDTH` are constants in the view, with the values and sources the contract gives (drifters/04-coin.md, palette and placeholder_look, guess). Sizes, ring and glint offsets come from the coin's fields, so no number from tuning is duplicated.
- The `Point` type alias is local to the view; the registry has no equivalent.
- The ring rect uses `//` on `ring_width` and `ring_height` as the contract writes it (they are even integers).
