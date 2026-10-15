Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the UI Developer's DRA-29-04 work (ship drawn as its inverted-T hitbox through `ui/shapes.py`), passed by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-29-04-ui-developer.md` (this file). Reviewed `game/ui/shapes.py` and `game/ui/ship_view.py` against `docs/contracts/DRA-29/tasks/DRA-29-04-ui-developer.md`, `docs/contracts/systems/objects.md` (`ui/shapes.py` block), `docs/contracts/systems/ship.md` (Interface, Presentation, Impact), `docs/design/gdd/04-ship.md` (hitbox, placeholder_look, rules 8 and 9), `game/CONTEXT.md`, `game/ruff.toml`, `game/core/collision.py` and `game/core/ship.py`.
3. **Checks:** By reading only. I worked out the acceptance output by hand from `SHIP_HITBOX` and `spawn()` at (320, 240): the bar is x 314 to 325, rows 224 to 255, and the foot is x 304 to 335, rows 244 to 255. The nine probe pixels give `[True, False, False, True, True, True, True, False, False]`, and 384 + 384 − 144 = 624. Both match the report. Both signatures match the contract word for word. The imports match the contract's lists. The colour is the only number. The Decisions match the code. I ran nothing.
4. **Assumptions:** The "11 passed" UI test count is the existing `test_error_screen.py` and `test_hud.py`. No ship-view test exists yet; DRA-29-09 adds it.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, with no change asked. See For QA.
7. **Status:** done.

## Findings
1. **note** `game/ui/ship_view.py:25`: the `draw_ship` docstring says "Boxes are centered on the ship." Only the bar is. The foot is centered in x but sits along the bottom, with its center at y + 10. The module docstring and the contract (`systems/ship.md`, Presentation) are correct. Rule: docstrings say what the code does. Source: `game/CONTEXT.md`, Docstrings. A more accurate wording would be "The hitbox is placed at the ship's center". Change: none.

## Checklist
1. Interface matches the contract: pass. `draw_shape(surface, color, shape, width=0)` and `draw_hitbox(surface, color, hitbox, width=0)` match `objects.md`. `draw_ship(surface, ship)` and `SHIP_COLOR` are unchanged, as `ship.md` requires.
2. UI/core split: pass. Both modules only draw. `draw_ship` reads the ship through `ship_hitbox(ship)` alone and copies no size or offset. Neither file mutates core, and neither imports `app`.
3. Fixed 60 Hz tick: n/a. Neither file has a timer or reads time.
4. Randomness: n/a. Neither file uses any.
5. Browser rules: pass. No sleep, thread, `await`, blocking call or audio. No path.
6. Numbers trace to the GDD: pass. `SHIP_COLOR` (255, 255, 255) comes from 04-ship.md, placeholder_look (guess). The box sizes come from core. The rounding follows the task's Do text exactly.
7. Pillars and locked decisions: pass. The look is the hitbox by construction, so the hitbox is never bigger than what the player sees (04-ship.md, rule 8; 07-objects.md, rule 8).
8. Smells: pass. The functions are small and fully type-hinted. There is no duplication, no dead code and no module-level state. `log` is defined and unused, which `game/CONTEXT.md`, Logging requires.
9. Decisions: pass. All five match the code: the `isinstance` dispatch to `_draw_box` and `_draw_circle`, `width` passed straight through, `SHIP_COLOR` kept, `draw_ship` reading only through `ship_hitbox`, and the imports.
10. Report claims match the files: pass. The acceptance output matches my hand calculation. The grep claims are consistent with the files. The docstrings no longer name a rectangle. The lint, typecheck and UI test claims are plausible for these files, but I did not run them.

## For QA
- Ship at spawn: run the acceptance command and confirm the probe list and the 624 count. The upper corners of the old 32 × 32 square must be empty.
- Ship against the left wall (x 16) and the right wall (x 624): the foot reaches column 0 or 639 exactly, and no pixel is lost or added.
- Ship at a half-pixel x, such as 320.5 or 321.5: the bar and the foot must round the same way, so the T never splits or shifts by 1 px between its parts.
- Ship partly below the floor: the drawing clips with no error. The blink still hides the whole T.
- `draw_shape` with `width=1` on a box and a circle: a 1 px outline with an empty center. DRA-29-06 relies on this.
