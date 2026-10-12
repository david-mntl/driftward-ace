Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-13-02-ui-developer.md` (UI Developer, task `docs/contracts/DRA-13/tasks/DRA-13-02-ui-developer.md`) against `docs/contracts/DRA-13/DRA-13-scroll.md`, Interface (`ui/starfield.py` block) and Presentation. Requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-13-02-ui-developer.md` (this file). Reviewed: `game/ui/starfield.py`. Read for reference: `game/core/scroll.py`, `game/core/world.py`, `game/ui/ship_view.py`, `game/ui/look.py`.
3. **Checks:** by reading only. Nothing run.
   - Interface: `STAR_COUNT`, `STAR_COLOR`, `STAR_SIZES`, `STAR_SEED`, `Star`, `STARS` and the `draw_starfield` signature checked against the contract line by line. They match.
   - Star layout order (`x`, `base_y`, `size` from one `random.Random(STAR_SEED)`) and the draw formula checked against Presentation and the task's Do. They match.
   - Acceptance figures recomputed by hand: `Scroll(ticks=40, scrolled_ticks=10).distance_px` is `10 * 1.1 = 11.000000000000002`, so `int((base_y + 11.000000000000002) % 480)` is `(base_y + 11) % 480`. Agrees with "same star at y+11 (mod 480)". 131 star pixels fits 50 stars with no overlap or clipping (23 of size 1, 27 of size 2).
   - Viewed the two PNGs the report names (`star0.png`, `star11.png` in the session scratchpad). About 50 dim dots over the whole screen; the second image is the first shifted down, with the bottom dots now near the top. Looking at an image is not running code.
   - Read against `game/CONTEXT.md` (logging, errors, layout), `game/ruff.toml` (py312, line 100, ANN), `15-tech-constraints.md`, `03-world-and-camera.md`, `12-art-and-audio.md`, the DRA-13 scope report, and the ui-developer standards in `.claude/agents/ui-developer.md`.
   - No data file is read, so no schema applies (`docs/contracts/schemas/` is empty).
   - 0 must-fix, 1 should-fix, 4 notes.
4. **Assumptions:**
   - Where the ui-developer standards ask for randomness from a passed-in `random.Random`, but the contract asks for a fixed-seed `random.Random` built inside the module, I treat the contract as the rule.
   - "Implementers' standards" means the Python and check rules in `.claude/agents/ui-developer.md`.
5. **Documentation differences:** None. The starfield values are not in the GDD on purpose: the scope report DRA-13 records them as temporary stand-ins the Director approved and chose to keep out of the GDD. `12-art-and-audio.md` keeps the black `placeholder_bg` underneath, which the code does not touch.
6. **Next:**
   - QA Engineer: run the checks for `docs/reports/implementation/ui/DRA-13-02-ui-developer.md`. Must-fix count: 0.
   - Integration Engineer: calling `draw_starfield` once per frame, after the background fill and before the ship and HUD, is in `game/app/` and not covered here. Pillar 2 (`12-art-and-audio.md`, rule 2) needs the starfield under hazards and warnings when they arrive.
7. **Status:** done.

## Findings
1. **should-fix** `docs/reports/implementation/ui/DRA-13-02-ui-developer.md:9`: the acceptance command is given as `python -c "..."`, with the script left out. The task asks to "Put the command and both image paths in the implementation report", and the standards ask for "the exact command under Checks so the Director can run it and see the numbers". As written, nobody can rerun it. Source: task DRA-13-02, Acceptance check; ui-developer.md, Checks before you report. Change: add the full inline script (or a fix section with it) so the Director can reproduce both PNGs.
2. **note** `game/ui/starfield.py:39`: the `random.Random` is built inside the module from `STAR_SEED`, not passed in. The ui-developer standards say visual randomness "comes only from a `random.Random` instance passed in". The contract asks for exactly this fixed-seed build, and no module-level `random.*` function is used. It never touches core. Source: DRA-13-scroll.md, Presentation (star layout); ui-developer.md, Browser and tick rules. Change: none.
3. **note** `game/ui/starfield.py:8,16`: `logging` is imported and `log` defined but never used. The contract's import line lists only pygame, random, `core.scroll`, `core.world`. `game/CONTEXT.md`, Logging, requires the module logger in every module with code, and `ship_view.py` does the same. The DRA-6-02 review raised the same note. Source: game/CONTEXT.md, Logging; DRA-13-scroll.md, Interface. Change: none.
4. **note** `game/ui/starfield.py:37-46`: `_build_stars()` is a module-level name the Interface doesn't list. It is private, runs once at import and only feeds `STARS`, so the public Interface is unchanged. Decisions explains it. Source: DRA-13-scroll.md, Interface; ui-developer.md, Outputs (never add to the Interface). Change: none.
5. **note** `docs/reports/implementation/ui/DRA-13-02-ui-developer.md:13`: standards check 5 asks to show core state "byte for byte unchanged" after the draw. The report argues it from `Scroll` being frozen instead of showing it. The argument holds: `Scroll` is `frozen=True` with two int fields (`core/scroll.py:36-44`), and `draw_starfield` only reads `distance_px` (`starfield.py:60`). Source: ui-developer.md, Checks before you report, item 5. Change: none. QA can confirm it.

## Checklist
1. Interface matches exactly: **pass**. `STAR_COUNT: int = 50` (`starfield.py:18`), `STAR_COLOR: tuple[int, int, int] = (90, 100, 140)` (`:22`), `STAR_SIZES: tuple[int, ...] = (1, 2)` (`:26`), `STAR_SEED: int = 1301` (`:30`), `Star = tuple[int, int, int]` (`:33`), `STARS: tuple[Star, ...]` (`:49`), `draw_starfield(surface: pygame.Surface, scroll: Scroll) -> None` (`:53`). Nothing renamed or dropped; the only extra name is private (note 4).
2. UI/core split: **pass**. The view reads `scroll.distance_px`, `SCREEN_W` and `SCREEN_H` only. No rule, timer, score or life count. Nothing is assigned to the scroll. `game/core/` has no `ui` import (grep, no hits).
3. Fixed 60 Hz tick: **pass**. No clock, frame time or frame counter. Star motion comes only from the core distance.
4. Randomness only from a passed-in `random.Random`: **finding** (note 2). Fixed-seed instance per the contract, built once at import. No `random.*` module function. Iteration over a tuple, so draw order is fixed and decides no outcome.
5. Browser rules: **pass**. No blocking call, sleep, thread, `await`, display flip, event or key polling, image or audio load, file path.
6. Every number traces to its source: **pass**. Count, color and sizes are the scope report DRA-13 stand-ins, and each docstring says so in the task's words (`starfield.py:19-20, 23-24, 27-28`). The seed has no design meaning, as the contract says. Screen size comes from `core.world`, never written as 640 or 480.
7. Pillars and locked decisions: **pass**. The view never changes the ship or the scroll (Pillar 1). The screen stays fixed; only dots move. Dim color keeps hazards readable later (Pillar 2, `12-art-and-audio.md` rule 2). Walls, weapons and hazard rules: n/a.
8. Smells: **pass**. Two short functions, two parameters each, one loop level, no duplication, no magic numbers, no dead or commented-out code. Module-level names are `log` and constants (`STARS` is an immutable tuple the contract allows). Every function and the non-obvious locals are typed. Lines are under 100.
9. Decisions present and matching the code: **pass**. Four bullets. Import style (`starfield.py:13-14`, same as `ship_view.py:12`), the helper and its order (`:41-45`), the value sources, and `int(...)` on y only with no background fill (`:62-63`) all match.
10. Report claims match the files: **finding** (should-fix 1). The pixel shift, color and image paths agree with the code and the images. The grep claims hold for `starfield.py` and `game/core/`. The command itself is elided. Nothing was run.

## For QA
- `start_scroll()`: exactly 50 stars at their base positions in (90, 100, 140), sizes 1 or 2 only, the same layout in two separate processes.
- `Scroll(ticks=40, scrolled_ticks=10)`: every star's top-left y is `(base_y + 11) % 480`; dots from the bottom 11 rows show near the top.
- Wrap edges: `base_y + distance_px` exactly 480.0 gives y 0; a 2 px star at y 479 is clipped to one row with no error.
- The draw leaves every non-star pixel unchanged (no fill), gives identical pixels when repeated, and leaves the `Scroll` equal to its input.
- A long run (for example `scrolled_ticks=216000`) still puts every star at y 0..479.
