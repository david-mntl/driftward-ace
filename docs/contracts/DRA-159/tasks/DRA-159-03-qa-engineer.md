Feature: DRA-159
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/mute-icon.md
Impact: docs/contracts/DRA-159/impact.md
Status: open
Linear: DRA-164

## Read in the contract
- mute-icon.md: Interface, game/ui/mute_icon.py, Rules, Look, Its size on screen, It blinks, Placement, The icon sits in the bottom-right corner, It adds no text anywhere, It never covers a pixel of the play area, Loading, The icon's rectangle must lie inside the window, Cost, Cheap to draw

## Builds
- `game/tests/ui/test_mute_icon.py` (new)
- `game/tests/CONTEXT.md` (changed): one line for the new file

## Depends on
DRA-159-01, DRA-159-02

## Not in the contract
- The main session's `game/tuning/mute_icon.json` must exist: the tests read `margin` and `size` from it, as the tests' rules say every number comes from tuning.

## Test
- `draw(window, False)` leaves every window pixel as it was. Rules: Look (the picture shows only while muted); Presentation
- `draw(window, True)` with an opaque stand-in puts the picture in the rectangle whose right and bottom edges sit `margin` from the window's right and bottom edges. Rules: Placement, 6
- With the music muted, no pixel outside that rectangle changes, the play area's included. Rules: Placement, 8 and 9
- Drawing twice, or a frame later, gives the same pixels: nothing in it changes. Rules: Look, 5
- A stand-in with a transparent region leaves the window pixels under that region as they were: the picture is blitted with its alpha. Rules: Cost, 18
- The shipped `game/assets/mute_icon.png` is exactly `size` x `size` from the tuning file, has an alpha channel, and holds both transparent and opaque pixels. Rules: Look, 2; Loading, 16
- The tuning file's `margin` and `size` put the rectangle inside the 856 x 518 window and clear of the play area's rectangle (the window and play area from `game/tuning/hud.json` and `core.world`). Rules: Loading, 15; Placement, 9

## Acceptance check
`game/tests/check.sh` ends `QA: pass` with the new tests in it.

## Out of scope
- Tests for the tuning loader, the picture loader, the frame loop's draw order, the dim or the M key: those are `game/app/` code and run in the browser at integration.
- Changing a contract, the tuning file or game code.
