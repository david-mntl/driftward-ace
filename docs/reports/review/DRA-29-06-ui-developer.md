Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review task DRA-29-06 (`draw_debug_hitboxes` in the debug overlay) against `docs/contracts/systems/debug-overlay.md` v3. The `/implement` skill asked for it in Review mode.
2. **Delivered:** `docs/reports/review/DRA-29-06-ui-developer.md` (this file). I reviewed `game/ui/debug_overlay.py`.
3. **Checks:** I compared, by reading only, the implementation report `docs/reports/implementation/ui/DRA-29-06-ui-developer.md`, the task file `docs/contracts/DRA-29/tasks/DRA-29-06-ui-developer.md`, the contract `docs/contracts/systems/debug-overlay.md` (Interface, Presentation, Rules, Impact, Rationale), `docs/design/gdd/10-ui.md` (debug_overlay, debug_overlay_color, debug_text_font), `game/CONTEXT.md`, `game/ruff.toml`, `game/ui/shapes.py`, `game/core/objects/base.py`, and the `Run` and `ship_hitbox` signatures in `game/core/`. Result: 10 checklist items, 8 pass, 2 n/a. 1 finding (note, no change). I ran nothing.
4. **Assumptions:** I took `draw_debug_overlay`, `overlay_text_bottom` and the constants as unchanged by reading them against the contract, not by diffing them. git status shows no change under `game/tests/`, so `test_hud.py` is untouched.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Nothing needs to change. The note below asks for no change.
7. **Status:** done.

## Findings
1. **note** `game/ui/debug_overlay.py:8-9`: the module docstring says the view never "changes the ship". Now that `draw_debug_hitboxes` takes the whole run, the contract's wording is "never changes the run" (debug-overlay.md, Presentation, last bullet). The code changes nothing: it only calls `draw_hitbox`, `font.render` and `blit`. The difference is in wording only. Rule: docstrings say what the code does. Source: game/CONTEXT.md, Docstrings. Change: none.

## Checklist
1. Interface matches the contract exactly: pass. `draw_debug_hitboxes(surface: pygame.Surface, run: Run) -> None` (`debug_overlay.py:62`). The other two functions and three constants keep the same signatures. The imports (`core.objects.base`, `core.run`, `ui.shapes`) are the ones the contract names. No `app` import.
2. UI/core split: pass. The view reads only `run.ship`, `run.objects`, `ship_hitbox`, `current_hitbox()`, `graze_zone()`, `object_type`, `variant`, `x`, `y`, `width`, `height` and `phase`. It computes only pixel positions (`:89-93`, `:102-103`). It mutates nothing, and `game/core/` doesn't import `ui`.
3. Fixed 60 Hz tick: n/a. No timers and no time in this view.
4. Randomness: n/a. No randomness. Iterating `run.objects` (a tuple) only sets draw order, as the contract requires.
5. Browser rules: pass. No sleep, thread, await, blocking call, audio, or file path.
6. Numbers trace: pass. Color, font and outline width 1 come from `OVERLAY_COLOR`, `_overlay_font()` and the contract's `draw_hitbox(..., 1)`. The label place uses only `obj.width / 2` and `obj.height / 2` (contract, Presentation, Label place). No new constant and no fallback.
7. Pillars and locked decisions: pass. Debug view only, with no rule change. Warning-phase objects draw no hitbox, because `current_hitbox()` returns `()`. That matches "warns before it strikes".
8. Smells: pass. Short functions, full type hints, no dead code, and no module-level state other than the `@cache` font the contract allows. The three loops over `run.objects` are the contract's draw order, not duplication.
9. Decisions: pass. All four match the code: the three loops (`:69-75`), the ship hitbox drawn with no visibility check (`:71`), the cached font with `z.2f` (`:84-86`), and the outlines through `ui.shapes.draw_hitbox` (`:70`, `:71`, `:73`).
10. Report claims match the files: pass. The acceptance output fits the code. The graze ring (r 28) covers rows 91-93 at x 320, the hitbox (r 14) covers rows 105-107, and the center stays unfilled because width is 1. The label's top-left is (306, 134). The ship's box edge falls on column 314, and the label runs past x 350. The clamp is `max(0, min(wanted, size - label size))` (`:102-103`), as the Assumptions say.

## For QA
- A meteorite in WARNING above the screen: no outline, and its label sits clamped against the top edge.
- An object near the left or right wall: the label stays fully on screen, with no part cut off.
- The ship blinking after a hit: its hitbox outline stays drawn on every frame.
- `tests/ui/test_hud.py` still passes unchanged, and `draw_debug_overlay` pixels are identical with or without objects.
- Several objects at once: every graze ring is drawn under every hitbox outline, and the labels are drawn last.
