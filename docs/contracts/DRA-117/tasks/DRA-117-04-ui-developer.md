Feature: DRA-117
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/hud.md
Impact: docs/contracts/DRA-117/impact.md
Status: open
Linear: DRA-121

## Read in the contract
- Purpose; Diagram (both layouts and the flowchart)
- Interface: the DRA-117 block (game/ui/score_text.py, game/ui/hud.py)
- Presentation: the row `run.grazes`; `graze_text(grazes)`; SCORE line (the line 2 bullet); GRAZE line
- Rules: the first two rules (what the HUD shows; GRAZE's stand-in) and Corner warnings
- Rationale: "GRAZE fills line 2's slot", "One grouping for SCORE and GRAZE"

## Builds
- `game/ui/score_text.py` (changed)
- `game/ui/hud.py` (changed)

## Depends on
DRA-117-02

## Not in the contract
None.

## Acceptance check
From `game/`, a headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report:
- prints `graze_text(n)` and `score_text(n)` for 0, 5, 999, 1000, 1234 and 1234567: the same digit groups after each label;
- draws the HUD for runs with `grazes` 0, 5 and 1234 in normal mode and in debug mode (`below_overlay` True, over the debug overlay), saves the PNGs outside the repo, and prints the bounding box of the GRAZE line's ink in each: its left at the margin, its top one HUD line below SCORE's, below the overlay's text in debug mode, and its bottom far above row 168.

Put the script, its output and the PNG names in the implementation report. `game/tests/check.sh lint` and `typecheck` pass; in `ui` the only failures are the `test_hud.py` ones `impact.md` expects from DRA-117-04.

## Out of scope
- LV, BEST, the HUD redesign, grazes on the Game Over box (scope report DRA-117, Out).
- The popup and the ring (DRA-117-03). `game/app/`, core, tests. Any change to the hearts or the SCORE line.
