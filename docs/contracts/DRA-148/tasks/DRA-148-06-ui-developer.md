Feature: DRA-148
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/level-up.md
Impact: docs/contracts/DRA-148/impact.md
Status: open
Linear: DRA-154

## Read in the contract
- level-up.md: `systems/level-up/view.md`: Interface (`LevelUpView.draw_flight`); Presentation (The flight; Cost; What the views never do)
- level-up.md: `systems/level-up/rationale.md`: "The flight ends on the pop's first size"

## Builds
- `game/ui/level_up_view.py` (changed): `draw_flight`, and the flight's pre-rendered sizes built in `__init__`

## Depends on
DRA-148-04, DRA-148-05

## Not in the contract
None.

## Acceptance check
From `game/`, a headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report builds the HUD and the view with the game's `hud.json` rules and art and a look of your own that satisfies the schema, then draws the window (HUD first, then `draw_flight`) for a banner at the ages from just before the flight's start to just after the arrival, saves the PNGs outside the repo and shows:
- nothing is drawn by `draw_flight` before the flight's start, on the arrival tick and after, or for None (the window is pixel-equal to the HUD alone);
- the number on the flight's start tick sits at its resting place, shrinks on every state, follows the arc, and its colors move toward the HUD's tier color;
- on the last flight state its center and size are the HUD level slot's center and the slot's size times the pop's start scale, within 1 px;
- after 500 draws across the flight no surface was built, no text rendered and no scale or rotate called.
`game/tests/check.sh lint` and `typecheck` pass.

## Out of scope
- The banner on the play area (task DRA-148-04) and the HUD pop (task DRA-148-05). The draw order and the app's call (the Integration Engineer's). Tests, the tuning file.
