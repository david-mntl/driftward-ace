Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-6-02-ui-developer.md` (UI Developer, task `docs/contracts/DRA-6/tasks/DRA-6-02-ui-developer.md`) against `docs/contracts/DRA-6/DRA-6-ship.md`, Interface and Presentation. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-6-02-ui-developer.md` (this file). Reviewed: `game/ui/ship_view.py`. Read for reference: `game/core/ship.py`, `game/ui/look.py`.
3. **Checks:** by reading only. Nothing run.
   - Interface: `SHIP_COLOR` (type, value) and the `draw_ship` signature checked against the contract line by line. They match.
   - Corner formula checked against Presentation. Reported pixel numbers recomputed by hand: spawn (320, 240) gives 304..335 × 224..255, 1024 px. (100.4, 400.6) gives 84..115 × 385..416. y 470 gives rows 454..479, 26 × 32 = 832 px. All agree with the code.
   - Read against `game/CONTEXT.md` (logging, errors, layout), `game/ruff.toml` (py312, line 100, ANN), `15-tech-constraints.md`, `04-ship.md` Values, and the ui-developer standards in `.claude/agents/ui-developer.md`.
   - No data file is read, so no schema applies (`docs/contracts/schemas/` is empty).
   - 0 must-fix, 0 should-fix, 4 notes.
4. **Assumptions:**
   - Where the ui-developer standards ask for a view class with `draw(surface, camera)` and `Vector2`/`FRect` positions, but the contract gives a plain function with no camera and float fields, I treat the contract as the rule.
5. **Documentation differences:** None.
6. **Next:**
   - QA Engineer: run the checks for `docs/reports/implementation/ui/DRA-6-02-ui-developer.md`. Must-fix count: 0.
   - Integration Engineer: calling `draw_ship` once per frame, after the background fill and before the flip, is in `game/app/` and not covered here.
7. **Status:** done.

## Findings
1. **note** `game/ui/ship_view.py:20-29`: a module-level function, not the view class with `draw(surface, camera)` that the ui-developer standards describe ("What you build": one view class per core entity, a camera transform). The contract's Interface gives `draw_ship(surface, ship)` and DRA-6 has no camera, so the code follows the contract. Decisions explains this. Source: DRA-6-ship.md, Interface; ui-developer.md, What you build. Change: none now. When the camera contract lands, the Architect decides whether the ship view becomes a class.
2. **note** `game/ui/ship_view.py:8,14`: the module imports `logging` and defines `log`, which `draw_ship` never uses. The contract's import line lists only pygame and `core.ship`. `game/CONTEXT.md`, Logging, requires the module logger in every module with code, and `ui/error_screen.py` does the same. Not a break: the contract names no logging rule that forbids it, and the view must not log per frame. Source: game/CONTEXT.md, Logging; DRA-6-ship.md, Interface. Change: none.
3. **note** `game/ui/ship_view.py:27-28`: Python's `round` uses half-to-even, so a corner at exactly .5 rounds to the even pixel (84.5 to 84, 85.5 to 86). The step stays monotonic, so no backward jitter, but sub-pixel steps across .5 values land unevenly. The contract names `round` and the implementer flagged this under Assumptions. Source: DRA-6-ship.md, Presentation and Rationale. Change: none. If the drift ever looks uneven in the browser, the Architect can name a different rounding.
4. **note** report, Checks line 10: `ruff format --check .` is reported as "18 files already formatted". I find 15 `.py` files under `game/` now. The gap may come from timing (the untracked `ui/debug_overlay.py` was appearing during that run) or from files I can't see. The claim is one the code can pass. Source: implementation-reviewer checklist item 10. Change: none. QA re-runs ruff.

## Checklist
1. Interface matches exactly: **pass**. `SHIP_COLOR: tuple[int, int, int] = (255, 255, 255)` (`ship_view.py:16`) and `draw_ship(surface: pygame.Surface, ship: Ship) -> None` (`ship_view.py:20`). Nothing renamed, added or dropped.
2. UI/core split: **pass**. The view reads `ship.x`, `ship.y`, `SHIP_W` and `SHIP_H` only. No rule, timer, score or life count. `Ship` is frozen and nothing is assigned to it. `game/core/` imports only stdlib and `core.world`.
3. Fixed 60 Hz tick: **pass**. No clock, frame time or timer in the view.
4. Randomness only from a passed-in `random.Random`: **n/a**. No randomness.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, display flip, event or key polling, image or audio load, file path.
6. Every number traces to the GDD: **pass**. `SHIP_COLOR` is 04-ship.md, placeholder_look (guess). Size comes from `core.ship` (04-ship.md, ship_w and ship_h, guess). 32 is never written in `game/ui/`. The `/ 2` is the contract's center-to-corner formula, not a tuning value.
7. Pillars and locked decisions: **pass**. The view draws only and changes no movement. Walls, weapons and hazard rules: n/a.
8. Smells: **pass**. One short function, two parameters, no nesting, no duplication, no magic numbers, no dead or commented-out code. Module-level names are `log` and one constant. Every function and the typed locals carry hints. Docstrings state units and sources.
9. Decisions present and matching the code: **pass**. All five bullets checked. Plain function, the ship passed in each call, rounding the corner and not the center, no fill, flip or logging in the draw, and the value sources all match the code.
10. Report claims match the files: **finding** (note 4, file count only). The acceptance and moved-ship pixel figures agree with the code by hand. The grep claims hold: no forbidden call in `game/ui/ship_view.py`, no `ui` import in `game/core/`. Nothing was run.

## For QA
- Spawn: one white 32×32 square on black, pixels (304, 224) to (335, 255), with nothing else drawn.
- Wall-clamped ships (x 16.0 and x 624.0): the square sits flush at columns 0..31 and 608..639, with no clipped column.
- A ship partly below the floor (y 470) draws 832 pixels, and no error is raised.
- `draw_ship` leaves every pixel outside the square unchanged (no background fill). Drawing the same ship twice gives identical pixels.
- A corner at exactly .5 (e.g. x 100.5 and 101.5) lands on 84 and 86. Confirm this is acceptable, or raise it to the Architect.
