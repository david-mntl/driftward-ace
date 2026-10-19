Status: ready-for-review
Created by: ui-developer

1. **Task:** `docs/contracts/DRA-76/tasks/DRA-76-06-ui-developer.md`: add `OVERLAY_TEXT_LINES`, `draw_debug_wave_lines` and the six-line `overlay_text_bottom` to the debug overlay (Architect, contract `docs/contracts/systems/debug-overlay.md` v4).
2. **Delivered:** `game/ui/debug_overlay.py` (changed).
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile game/ui/debug_overlay.py`: clean.
   - `ruff check game` and `ruff format --check game` (run from `game/`): all checks passed, 68 files formatted.
   - Acceptance command, run from `game/` exactly as in the task (`SDL_VIDEODRIVER=dummy python -c "..."`). Output:
     ```
     True True True
     True
     ```
     Lines 5 and 6 read `wave none` / `level 1` with no waves, `wave wave_0` / `level 1` while a wave plays, `wave rest` / `level 3` during a rest, byte-identical to the expected render. `overlay_text_bottom()` equals `OVERLAY_MARGIN + 5 * line + max(line, font height)`.
   - Follows the state: the three runs draw three different pictures (the three `True` compare against three different expected renders). The resting run's `repr` is identical before and after the draw.
   - `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core and ui PASS. `tests/ui/test_hud.py` passed unchanged (13 tests).
   - Grep of `game/ui/` for the banned calls: the only hits are `run.waves` at `debug_overlay.py:159,161`, matched by the `.wav` pattern (regex dot). No real hit. Grep of `game/core/` for `game.ui` and `ui` imports: no hits.
4. **Assumptions:** None. No screenshot taken; the byte comparison against the expected render is the proof.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-76/tasks/DRA-76-06-ui-developer.md`. Left alone: `draw_debug_hitboxes` body, `game/ui/hud.py`, and `game/app/frame.py`. The Integration Engineer must call `draw_debug_wave_lines(surface, run)` right after `draw_debug_overlay`; until then lines 5 and 6 are not drawn and the HUD sits two empty lines lower in debug mode.
7. **Status:** done.

## Decisions
- `draw_debug_wave_lines` reads only `run.waves` (None gives `none`), `run.waves.current_wave_id` (None gives `rest`) and `run.level`. It computes nothing else. Source: contract, Presentation.
- `OVERLAY_TEXT_LINES = 6`, and `overlay_text_bottom()` uses `(OVERLAY_TEXT_LINES - 1) * linesize`. Source: contract, Interface.
- A private helper `_draw_text_line(surface, text, index)` renders and places one text line. `_draw_text` (lines 1 to 4) and the wave lines both use it, so the line placement is not written twice. The pixels of lines 1 to 4 are unchanged (`test_hud.py` passes untouched).
- `FIRST_WAVE_LINE = 4` is the index of line 5. It is a position constant from the contract's layout (line 5 at `OVERLAY_MARGIN + 4 x linesize`), not a tuned value.
- Font, color and margin are the existing `_overlay_font()`, `OVERLAY_COLOR` and `OVERLAY_MARGIN` (10-ui.md, guess values). The two lines are rendered each frame; only the font is cached.
- The module docstring now names `draw_debug_wave_lines`, as the contract's Impact table asks.
