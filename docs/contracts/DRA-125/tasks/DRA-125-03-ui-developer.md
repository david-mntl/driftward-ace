Feature: DRA-125
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/run.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-129

## Read in the contract
- Interface, "DRA-125: what the last life adds and changes": the `core/last_life.py` block (`Burst`) and the `ui/burst_view.py` block
- Presentation: the `run.burst`, `run.last_life` row; Burst
- Rules: Burst
- Rationale: "The burst lives in core, its look in the view"

## Builds
- `game/ui/burst_view.py` (new)

## Depends on
DRA-125-01

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report draws `start_burst(LastLifeRules(), 320, 240)` stepped to ages 0, 30, 60 and 119 on a black 640 × 480 surface, and `start_burst(LastLifeRules(), 320, 480)` at age 30, and saves each as a PNG outside the repo. For each it prints the number of separate square blobs on the surface, the center of each, and the max channel value of its pixels: 12 blobs on the origin's circle (fewer after the bottom-edge burst, whose lower half is off the canvas), at the radius the age gives, getting fainter with age. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- The screen flash, the HUD life break, the real burst and the rebuild (LD-08).
- Drawing the burst in the frame (the Integration Engineer's), core, tests.
