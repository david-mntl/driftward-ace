Feature: DRA-117
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/run.md
Impact: docs/contracts/DRA-117/impact.md
Status: open
Linear: DRA-120

## Read in the contract
- Interface, "DRA-117: what graze adds and changes": the core/graze.py block (GrazeRing), the core/popup.py block (PopupKind), the game/ui/popup_view.py block and the game/ui/graze_view.py block
- Presentation: the rows `popup.kind` and `run.graze_rings`; Points popup (for what stays as it is); Graze popup; Graze ring
- Rationale: "Popups have a kind; colors stay in the view", "Graze popups share the coins' layer", "The ring follows the ship through the view"

## Builds
- `game/ui/popup_view.py` (changed)
- `game/ui/graze_view.py` (new)

## Depends on
DRA-117-02

## Not in the contract
None.

## Acceptance check
From `game/`, a headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report draws on a black 640 × 480 surface and saves the PNGs outside the repo, then lists what each shows:
- a coin popup and a graze popup of the same points side by side: the coin's in the coin color, the graze's in `GRAZE_POPUP_COLOR`, the same text size;
- one `GrazeRing` drawn at every age from 0 to its last state, around a ship at (320, 240), each in its own frame: for each, the radius of its ink and the color of one ink pixel, the radius growing and the color fading toward black state by state;
- the same ring drawn twice at one age: the second draw builds no new surface (the cache).

Put the script, its output and the PNG names in the implementation report. `game/tests/check.sh lint` and `typecheck` pass; `core` and `ui` have only the failures `impact.md` expects.

## Out of scope
- The HUD and `score_text` (DRA-117-04). `game/app/` (the draw call is the Integration Engineer's). Core, tuning files, tests.
- Any change to the coin popup's look, the ship view or the debug overlay.
