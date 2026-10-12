Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-6-04-ui-developer.md` (UI Developer, task `docs/contracts/DRA-6/tasks/DRA-6-04-ui-developer.md`) against `docs/contracts/DRA-6/DRA-6-debug-overlay.md`. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-6-04-ui-developer.md` (this file). Reviewed: `game/ui/debug_overlay.py`.
3. **Checks:** by reading only. Nothing run.
   - Interface: the three constants (names, types, values) and `draw_debug_overlay(surface: pygame.Surface, ship: Ship) -> None` checked against the contract. They match.
   - Presentation traced line by line: rows `TOP_LINE_Y` and `SCREEN_H - 1` from `core.world`, width from `surface.get_width()`, lines before text, text at (4, 4) stepping by `get_linesize()`, `f"{value:.2f}"`, default font at 16, antialiased, one color.
   - Read against 10-ui.md (debug_overlay, debug_overlay_layout, debug_text_font, debug_overlay_color, rules 5 and 7), 91-decision-log.md row 20, 15-tech-constraints.md rules 5 and 7, `game/CONTEXT.md` (logging, errors, run modes), `game/ruff.toml`, `game/tests/conftest.py` (font lifetime).
   - The report's grep claims re-checked with the same patterns over `game/ui/` and `game/core/`: no hits, as stated.
   - 0 must-fix, 0 should-fix, 2 notes.
4. **Assumptions:**
   - Stdlib imports (`logging`, `functools`) do not break the contract's import list ("pygame, core.ship, core.world. Never app."). That list fences off `app` and other game packages. `logging` is required by `game/CONTEXT.md`.
   - A process-lifetime font cache counts as a resource, not module-level game state.
5. **Documentation differences:** None. The contract, 10-ui.md, decision-log row 20 and the task agree. Note 1 is a question for the Architect, not a conflict.
6. **Next:**
   - QA Engineer: run the checks for `docs/reports/implementation/ui/DRA-6-04-ui-developer.md` (task DRA-6-03). Must-fix count: 0.
   - Architect (through the Director): optional. Decide whether `vx -0.00` is the wanted readout (note 1).
7. **Status:** done.

## Findings
1. **note** `game/ui/debug_overlay.py:68`: `f"{value:.2f}"` prints `-0.00` for any small negative value. Drag (`DRAG_X` 0.94, `core/ship.py:118`) shrinks vx toward 0 but never reaches it, so after the player lets go of Left the overlay reads `vx -0.00` for a long time. Moving right gives `vx 0.00`. The code does exactly what the contract asks. Rule: DRA-6-debug-overlay.md, Presentation ("Numbers use Python's `f"{value:.2f}"`"). Source: same; 04-ship.md, drag_x. Change: none in this task. If the Director wants `0.00`, the Architect adds a rule, for example normalizing `-0.0` after rounding.
2. **note** `game/ui/debug_overlay.py:73-80`: `functools.cache` keeps one `Font` for the life of the process. This meets "created once, on the first draw, and kept" (contract, Presentation; 15-tech-constraints.md, rule 5). The implementer flagged the limit under Assumptions: after `pygame.quit()` and a new `pygame.init()`, the cached font belongs to the old font module. No game code calls `pygame.quit()`. The test fixture `pygame_headless` is session-scoped (`game/tests/conftest.py:23-30`), so tests init once and quit once. Source: DRA-6-debug-overlay.md, Presentation. Change: none. QA should not add a per-test pygame init and quit around overlay tests without clearing the cache (`_overlay_font.cache_clear()`).

## Checklist
1. Interface matches exactly: **pass**. `OVERLAY_COLOR: tuple[int, int, int] = (0, 255, 0)`, `OVERLAY_FONT_SIZE: int = 16`, `OVERLAY_MARGIN: int = 4` (`debug_overlay.py:19-29`). `draw_debug_overlay(surface: pygame.Surface, ship: Ship) -> None` (`:32`). Nothing renamed, added or dropped. `_draw_lines`, `_draw_text`, `_overlay_font` and `log` are private or required by `game/CONTEXT.md`.
2. UI/core split: **pass**. The view reads `ship.x`, `ship.y`, `ship.vx`, `ship.vy` and two `core.world` constants and computes only pixel positions. No rule, timer or life count. `Ship` is frozen and never written. No `app` import, no run-mode read. `game/core/` has no `ui` import.
3. Fixed 60 Hz tick: **pass**. No clock, frame time or tick count in the module.
4. Randomness: **n/a**. None used. The readings tuple has a fixed order.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, audio, image load or file path. No `pygame.display`, `event` or `key` use.
6. Every number traces to the GDD: **pass**. Color, font size and margin each cite 10-ui.md (guess) in their docstrings. Rows come from `TOP_LINE_Y` and `SCREEN_H` (`:15`, `:51`). The `- 1` in `:50-51` is the last-pixel and last-row index, as the contract states. No 168, 479 or 640 literal. No fallback default.
7. Pillars and locked decisions: **pass**. Debug-only view, reads state only (10-ui.md, rules 5 and 7). No game rule touched. Weapons, walls and hazards: n/a.
8. Smells: **pass**. Three short functions, nesting one loop deep, no duplicated blocks, no magic numbers, no dead or commented-out code. Module-level state is the constants, `log` and the font cache (note 2). Every function and local is type-hinted. `log` is unused, which `game/CONTEXT.md` allows: the module has code, and the view has no event to log.
9. Decisions present and matching the code: **pass**. All six bullets checked: values and sources (`:19-29`, `:15`), lines then text (`:40-41`), the two helpers, the `(name, value)` tuple with one f-string loop (`:61-70`), the narrow imports (`:9-15`), and no fill, flip or `except`.
10. Report claims match the files: **pass**. The grep claims hold. Text tops 4, 16, 28, 40 follow from `OVERLAY_MARGIN + index * get_linesize()` with a line size of 12. `hits=4, misses=1` after five calls is what `functools.cache` gives. The draw-twice and no-mutation claims follow from the code. Nothing was run.

## For QA
- Spawn draw on 640×480: full-width (0, 255, 0) rows at exactly 168 and 479, nothing on 167, 169 or 478. Four text bands at the top-left with ink in green shades only.
- Surface wider than 640 (e.g. 800×600): lines span the full width, and the floor line stays on row 479, not 599, because it reads `SCREEN_H`.
- Negative values: `Ship(x=12.5, y=199.0, vx=-3.25, vy=-0.26)` reads `vx -3.25`, `vy -0.26`. A tiny negative such as vx -0.001 reads `vx -0.00` (note 1).
- The overlay leaves pixels outside the text bands and the two rows untouched: no fill.
- Font reuse: across many draws `_overlay_font()` returns the same object. Keep the session-scoped pygame fixture (note 2).
