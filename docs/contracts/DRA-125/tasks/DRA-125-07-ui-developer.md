Feature: DRA-125
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-133

## Read in the contract
- Interface: the `ui/pause_box.py` block; the `ui/screen_look.py` block (built in DRA-125-04)
- Presentation: the `flow.screen` PAUSED row; the shared items (Text, Box, Cache, Only draws); Pause box

## Builds
- `game/ui/pause_box.py` (new)

## Depends on
DRA-125-04

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report fills a 640 × 480 surface with a mid gray, calls `draw_pause_box`, and saves the image as a PNG outside the repo. It prints the box's darker rectangle (its rows and columns, and the gray inside and outside it) and the ink box of the PAUSE text: the box centered on the surface, the text centered on the box's center. The Director can open the PNG. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- Pause options (scope report DRA-125, Out). The real look (UI-04).
- Calling `draw_pause_box` from the frame (the Integration Engineer's), core, tests.
