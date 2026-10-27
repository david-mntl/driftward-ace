Feature: DRA-126
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/hud.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-141

## Read in the contract
- Purpose; Diagram (normal mode, the flowchart)
- Interface: "DRA-126 adds and changes" (`ui/score_text.py` and `ui/hud.py` blocks)
- Presentation: the `flow.best` row; `group_digits(number)` and `best_text(best)`; BEST line; SCORE line (`hud_top`); Both
- Rules: the BEST items and "Corner warnings, by Director override"
- Rationale: "`best` is a plain parameter with a default"; "`group_digits` made public"

## Builds
- `game/ui/score_text.py` (changed)
- `game/ui/hud.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report prints `group_digits` and `best_text` for 0, 999, 1 000, 1 234 and 1 000 007, then draws the HUD on a 640 × 480 surface for one run with `best` None and `best` 2 345, with `below_overlay` False and True, and saves each as a PNG outside the repo. It prints the ink box of the BEST text: its left edge at `HUD_BEST_X` and its rows those of the SCORE line in both modes, and no ink there with `best` None. The Director can open the PNGs. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- Passing `flow.best` to `draw_hud` (the Integration Engineer's). The leaderboard's use of `group_digits` (DRA-126-05). The HUD's real look and the long-SCORE overlap (UI-01). The corner warnings (docs/TODO.md).
- Core, tests.
