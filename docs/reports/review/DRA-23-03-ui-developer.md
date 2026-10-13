Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-23-03-ui-developer.md` (UI Developer, task `docs/contracts/DRA-23/tasks/DRA-23-03-ui-developer.md`) against `docs/contracts/systems/run.md`, Interface (`ui/game_over.py` block) and Presentation. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-23-03-ui-developer.md` (this file). Reviewed: `game/ui/game_over.py`.
3. **Checks:** by reading only. Nothing run.
   - The seven constants (`game_over.py:16-42`) match the contract's Interface in name, type and value. `draw_game_over(surface: pygame.Surface) -> None` (`:60`) matches.
   - Each constant docstring names scope report DRA-23, Game Over box, temporary stand-in approved by the Director, not in the GDD (UI-04 is TBD). That matches the task's Do and scope report DRA-23, Values needed (line 82). 10-ui.md, `game_over_screen` is TBD (UI-04). Nothing from the GDD is filled in.
   - Layout (`:69-77`): box top-left `((w - 320) // 2, (h - 120) // 2)` from `BOX_SIZE`, `title_top = box_top + (120 - block_height) // 2`, `block_height` = title `get_linesize()` + prompt `get_height()` (`:91`, `:97`), prompt top one title line-size below the title top, both centered on `width // 2`. Matches run.md, Presentation, line by line.
   - Build once: `@cache` on `_parts()` (`:80`), the same pattern as `ui/hud.py:57`. Box is `pygame.SRCALPHA` filled with `BOX_COLOR` (`:89-90`). Texts are antialiased (`True`) in `TEXT_COLOR` (`:94-95`).
   - Imports (`:8-12`): `logging`, `dataclasses`, `functools`, `pygame`. No `core`, no `app`. No fill of the target surface, no flip, no log call, no `try`, no key or mode read.
   - Acceptance numbers are consistent by arithmetic: (90, 100, 140) × (165/255) ≈ (58.2, 64.7, 90.6), so the printed (58, 64, 90) is the expected rounding of "about (58, 65, 91)". The printed text bbox (x 251 to 387, rows 225 to 254) lies inside the box (x 160 to 479, rows 180 to 299).
   - Lint pass is plausible: imports sorted stdlib then third-party, every function annotated, longest line under 100.
   - 0 must-fix, 0 should-fix, 3 notes.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: run the checks for `docs/reports/implementation/ui/DRA-23-03-ui-developer.md`. Must-fix count: 0.
7. **Status:** done.

## Findings
1. **note** `game/ui/game_over.py:87-88`: the two fonts are local to `_parts()` and dropped after rendering. Only the rendered texts and the two line sizes are kept. The contract says "both fonts and both rendered texts are built once, on the first draw, and kept" (run.md, Presentation, Rules for the view). The effect is the same: nothing is rebuilt per frame, and the fonts are never needed again. The implementation report's Assumptions (report line 20) says "only the box, fonts and rendered texts are cached", which does not match the code: the fonts are not cached. Rule: report claims match the files; build once (15-tech-constraints.md, rule 5). Source: run.md, Presentation; implementation report, Assumptions. Change: none needed in code. The report wording could say "the box, the rendered texts and the line sizes".
2. **note** `game/ui/game_over.py:63`: the `draw_game_over` docstring states the box corner with the literals 320 and 120, while the code reads `BOX_SIZE` (`:70`). If `BOX_SIZE` changes when UI-04 is decided, the docstring goes stale. Rule: no magic numbers (implementer standards, checklist item 8). Source: game/CONTEXT.md, Good practice. Change: write `((width - BOX_SIZE[0]) // 2, (height - BOX_SIZE[1]) // 2)` in the docstring.
3. **note** `game/ui/game_over.py:14`: `log` is defined and never used. That is what game/CONTEXT.md, Logging requires for a module with code, and the view must not log per frame (run.md, Presentation). The Decisions note says so. Rule: module logger. Source: game/CONTEXT.md, Logging. Change: none.

## Checklist
1. Interface matches exactly: **pass**. Seven constants (`:16`, `:20`, `:24`, `:28`, `:32`, `:36`, `:40`) and `draw_game_over` (`:60`) match run.md, Interface. `_Parts` and `_parts()` are private helpers, not part of the interface.
2. UI/core split: **pass**. No rule, timer or life count. The view reads no core state and imports nothing from `core` or `app`. No change in `game/core/` from this task.
3. Fixed 60 Hz tick: **n/a**. No timing in the view.
4. Randomness only from a passed-in `random.Random`: **n/a**. No randomness.
5. Browser rules: **pass**. No sleep, thread, `await`, file load or audio. No path used.
6. Every number traces to its source: **pass**. Every value traces to scope report DRA-23, Values needed (Game Over box), as the task and contract require. Layout arithmetic uses `BOX_SIZE` and font metrics only. Docstring literals: note 2.
7. Pillars and locked decisions: **pass**. The box is see-through (alpha 90), so the frozen frame stays visible behind it, as the scope report asks. Retry wording names the arrows only (locked decision 1). No hazard, wall or movement touched.
8. Smells: **pass**. One short public function, one cached builder, a frozen dataclass. No nesting, no duplication, no dead code. The `@cache` holds rendered surfaces, not game state. Type hints on every function and local. Notes 2 and 3.
9. Decisions present and matching the code: **pass**. Five Decisions. Each matches: `@cache` on `_parts()` returning frozen `_Parts` (`:45`, `:80`); size read at draw time (`:69`); vertical layout (`:74-77`); sources copied from task and contract; unused logger, no `try`.
10. Report claims match the files: **finding** (note 1). Delivered, Checks and the grep claims match the file as read. The Assumptions line says fonts are cached; they are not.

## For QA
- Draw the box twice, the second time after a retry: `_parts()` returns the same object, and the result looks the same (no per-frame build).
- Draw on a surface that is not 640 × 480 (for example 800 × 600): box top-left is ((w - 320) // 2, (h - 120) // 2) and both texts stay centered inside it.
- Over a non-black fill, a pixel inside the box away from the text is darker and a pixel outside is unchanged; the target surface is never filled or flipped.
- The white text bbox lies inside the box rows 180 to 299 on 640 × 480, with the prompt below the title and both centered on x 320.
- Calling `draw_game_over` before `pygame.font.init()` should raise, not be caught.
