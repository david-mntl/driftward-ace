Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-13-03-ui-developer.md` (UI Developer, task `docs/contracts/DRA-13/tasks/DRA-13-03-ui-developer.md`) against `docs/contracts/DRA-13/DRA-13-hud.md` and `docs/contracts/DRA-6/DRA-6-debug-overlay.md` (the `overlay_text_bottom()` addition). Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-13-03-ui-developer.md` (this file). Reviewed: `game/ui/hud.py`, `game/ui/debug_overlay.py`. Read for reference: `game/core/scroll.py`, the scratch script `hud_check.py` and the two PNGs the report names.
3. **Checks:** by reading only. Nothing run.
   - Interface: the six `HUD_*` constants (names, types, values) and `draw_hud(surface: pygame.Surface, scroll: Scroll, below_overlay: bool) -> None` checked line by line against DRA-13-hud.md. They match. `overlay_text_bottom() -> int` matches DRA-6-debug-overlay.md v1.
   - Layout math checked by hand against the report's numbers: `overlay_text_bottom()` = 52 fits `4 + 3*12 + 12` (linesize 12). Debug `hud_top` = 56, readout blit at y 76, white rows 79 to 84. Normal readout blit at y 24, white rows 27 to 32. Both end far above row 168.
   - `Scroll(ticks=130, scrolled_ticks=100).meters`: `floor(110.00000000000001 / 10)` = 11. Agrees with `11 m`.
   - Viewed `hud_normal.png` and `hud_debug.png` in the session scratchpad: white `0 m` top-left alone; four green lines, then white `11 m` clearly below them, then the top line at 168. Looking at an image is not running code.
   - `debug_overlay.py`: constants, `draw_debug_overlay`, `_draw_lines`, `_draw_text` and `_overlay_font` read against DRA-6-debug-overlay.md Interface and Presentation. Nothing beyond the new function differs from the contract. No git diff was run.
   - Read against `game/CONTEXT.md`, `game/ruff.toml` (py312, line 100, ANN), `10-ui.md`, the DRA-13 scope report and `.claude/agents/ui-developer.md`. Longest lines: `hud.py:44` at 95, `debug_overlay.py:45` at 98, both under 100.
   - No data file is read, so no schema applies.
   - 0 must-fix, 0 should-fix, 5 notes.
4. **Assumptions:**
   - Where the ui-developer standards and the contract differ (font passed in vs. built once on first call; no boolean flags vs. `below_overlay: bool`), I treat the contract as the rule and record a note.
   - The HUD values are not in the GDD on purpose (10-ui.md `hud_font_size_color` is TBD, UI-01). The scope report DRA-13 records them as Director-approved stand-ins kept out of the GDD. I treat that as a traced source, not a filled-in TBD.
5. **Documentation differences:** None.
6. **Next:**
   - QA Engineer: run the checks for `docs/reports/implementation/ui/DRA-13-03-ui-developer.md`. Must-fix count: 0.
   - Integration Engineer: `below_overlay` must come from the run mode, never from `overlay_visible`, and the HUD draws after the overlay (DRA-13-hud.md, Rules). Both live in `game/app/` and are not covered here.
7. **Status:** done.

## Findings
1. **note** `game/ui/hud.py:22-24`: the `HUD_FONT_SIZE` docstring calls it "HUD layout approved by the Director". The scope report lists the 16 px default font under "Meters readout text", a temporary stand-in, and the contract's Interface comment says "readout text: default font, 16 px". The task lets the docstring say either phrase, so this is wording only. Source: task DRA-13-03, Do; scope report DRA-13, Values needed. Change: say "temporary stand-in (readout text)", as `HUD_COLOR` does.
2. **note** `game/ui/hud.py:57-63`: the font is built inside the module on the first call and cached, not passed in. The ui-developer standards say a `pygame.font.Font` "is passed in. Never build one inside a draw call." The contract and task ask for exactly this "once, on the first call" pattern, and `debug_overlay.py:85-92` does the same. Not built per frame. Source: DRA-13-hud.md, Presentation; ui-developer.md, pygame-ce rules. Change: none.
3. **note** `game/ui/hud.py:43,50-52`: `below_overlay: bool` switches the layout. The standards say "no boolean flags that switch behavior". The contract's Interface names this parameter and its Rationale explains why the app passes it. Source: DRA-13-hud.md, Interface and Rationale; ui-developer.md, Python standards. Change: none.
4. **note** `game/ui/hud.py:8,16`: `logging` is imported and `log` defined but never used. `game/CONTEXT.md`, Logging, asks for the module logger in every module with code, and the contract forbids per-frame logging, so an unused logger is expected. The DRA-13-02 review raised the same note. Source: game/CONTEXT.md, Logging. Change: none.
5. **note** `docs/reports/implementation/ui/DRA-13-03-ui-developer.md:8`: the command runs `<scratch>/hud_check.py`, a file in the session scratchpad. It exists now and matches the task's steps, but nobody can rerun it once the scratchpad is gone. The standards ask for the exact command so the Director can see the numbers. Source: ui-developer.md, Checks before you report. Change: inline the script in a later report if this check has to be rerun.

## Checklist
1. Interface matches exactly: **pass**. `HUD_COLOR` (`hud.py:18`), `HUD_FONT_SIZE` (`:22`), `HUD_MARGIN` (`:26`), `HUD_LINE_SPACING` (`:30`), `HUD_TOP` (`:34`), `HUD_OVERLAY_GAP` (`:38`), `draw_hud` (`:43`), `overlay_text_bottom` (`debug_overlay.py:44`). Only the private `_hud_font` is extra. Imports are pygame, `core.scroll`, `ui.debug_overlay` and stdlib. No `app`.
2. UI/core split: **pass**. `draw_hud` reads only `scroll.meters` (`hud.py:53`) and formats it. No rule, timer or count. `Scroll` is frozen, and nothing is assigned. `game/core/` has no `ui` import.
3. Fixed 60 Hz tick: **pass**. No clock or frame time. The readout comes from the core distance.
4. Randomness only from a passed-in `random.Random`: **n/a**. No randomness.
5. Browser rules: **pass**. No sleep, thread, `await`, flip, event, key, image or audio load, file path.
6. Every number traces to its source: **pass**. All six HUD values come from the scope report DRA-13 stand-ins and HUD layout, as the contract says. Each docstring says so (wording, note 1). `overlay_text_bottom()` uses only `OVERLAY_MARGIN` and font metrics.
7. Pillars and locked decisions: **pass**. The HUD ends at row ~84 in debug mode and ~32 in normal mode, far above the top line at 168 (10-ui.md rule 1; Pillar 2). It changes no state (Pillar 1). Walls, weapons, hazards: n/a.
8. Smells: **finding** (notes 2, 3, 4). Short functions, no nesting, no duplication, no magic numbers, no dead code. Every function typed. The only module-level state is the `@cache` font, which the contract asks for.
9. Decisions present and matching the code: **pass**. Font cache (`hud.py:57`), import style (`:13-14`), value sources (`:18-40`), line 1 left empty by offsetting line 2 (`:54`). All match.
10. Report claims match the files: **finding** (note 5). The numbers agree with the code, the hand math and the PNGs. The grep claims hold for `hud.py` and `game/core/`. Lint pass is plausible from reading. Nothing was run.

## For QA
- Normal mode: `draw_hud(start_scroll(), below_overlay=False)` blits at (4, 24), and no pixel changes above row 24 or at row 168 and below.
- Debug mode: the lowest white pixel row is strictly greater than the overlay's lowest green text row, and below `overlay_text_bottom() + HUD_OVERLAY_GAP + HUD_LINE_SPACING`.
- `overlay_text_bottom()` gives the same value before and after `draw_debug_overlay`, and calling it draws nothing.
- Meters edges: `scrolled_ticks` 9 shows `0 m`, 10 shows `1 m`. Check for float drift on large counts, for example `scrolled_ticks=216000` shows `23760 m`.
- The draw leaves the `Scroll` equal to its input, gives identical pixels when repeated, and never fills the background.
