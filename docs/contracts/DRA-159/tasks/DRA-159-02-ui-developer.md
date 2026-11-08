Feature: DRA-159
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/mute-icon.md
Impact: docs/contracts/DRA-159/impact.md
Status: open
Linear: DRA-163

## Read in the contract
- mute-icon.md: Interface, game/ui/mute_icon.py; Presentation; Rules, Look (2 and 5); Rules, Placement (6, 8 and 9); Rules, Cost (18 and 19)

## Builds
- `game/ui/mute_icon.py` (new): `MuteIconLook` and `MuteIconView`

## Depends on
None

## Not in the contract
- The acceptance script uses a stand-in picture, a plain `size` x `size` surface made in the script, because the real picture comes from DRA-159-01 and its loader from the Integration Engineer. Source: mute-icon.md, Interface (the view takes an already-made surface, and the loader checks it).

## Acceptance check
A headless script (in the implementation report) opens an 856 x 518 window, builds a `MuteIconView` with `margin` and `size` read from `game/tuning/mute_icon.json` and the stand-in picture, and prints: `draw(window, False)` leaves every window pixel as it was; `draw(window, True)` changes pixels only inside the `size` x `size` rectangle whose right and bottom edges are `margin` px from the window's right and bottom edges; a second `draw(window, True)` gives the same pixels; a stand-in with a transparent region leaves the window pixels under it. `game/tests/check.sh lint` and `typecheck` pass.

## Out of scope
- Loading the tuning file or the picture, the draw call in the frame loop, the dim, the M key and any `game/app/` code. Those are Integration Engineer work.
- Any state, any motion, any text, any scaling, any color in code.
- The picture itself and the tuning file.
