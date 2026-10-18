Status: ready-for-review
Created by: ui-developer

1. **Task:** build the points popup's view, `popup_view.py`, from `docs/contracts/DRA-62/tasks/DRA-62-04-ui-developer.md` (Architect).
2. **Delivered:**
   - `game/ui/popup_view.py` (new): `POPUP_COLOR`, `POPUP_FONT_SIZE`, `popup_text`, `draw_points_popup`, plus two private cached helpers (`_popup_surface`, `_popup_font`).
3. **Checks:** run from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile ui/popup_view.py`: clean.
   - `tests/check.sh lint` (ruff check + format): pass. `tests/check.sh typecheck` (mypy strict): pass, 62 files.
   - Acceptance command (the one in the task, `SDL_VIDEODRIVER=dummy python -c "..."`), output: `+50 +100 True`.
   - Follows the state (inline run): a `+100` popup at age 0 has its ink at rows 161..166; at age 20 the same ink is at rows 151..156, so it rose exactly 10 px (20 x 0.5). Same state drawn twice: identical bytes. `repr(popup)` identical before and after the draw. Cache after drawing 100, 50, 100 (plus the earlier draws): 2 entries, 2 renders, 3 hits.
   - Grep of `game/ui/popup_view.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `game.ui` / `from ui` / `import ui`: no hits.
   - No screenshot saved.
4. **Assumptions:** none. `@cache` (unbounded) keeps one text per points value, as the contract's Cache line says; only 50 and 100 occur in play.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-62/tasks/DRA-62-04-ui-developer.md`. Drawing the popups each frame and their layer is the Integration Engineer's (`game/app/frame.py`); until then popups are not on screen. Left alone: `coin_view.py`, every core and app file, tests.
7. **Status:** done.

## Decisions
- Constants typed `Final` as the contract's Interface gives them (`hud.py` leaves its constants plain; the contract wins). Color source: drifters/04-coin.md, popup_color (guess). Size source: scope report DRA-62, Limits (the HUD's 16 px).
- Text uses `f"+{points}"`: a plus and decimal digits, no space, no grouping (run.md, Presentation, Text).
- Place is `round(popup.x)`, `round(popup.y)` on the text rect's center, as the contract says. `popup.y` is read from core each draw; nothing is copied or moved.
- The font and the text surfaces are cached with `functools.cache`, the same pattern `hud.py` uses for its font. The render is antialiased with no outline, shadow or fade.
- The module has no per-frame allocation beyond the rect `get_rect` makes. `draw_points_popup` only blits.
