Feature: DRA-148
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/level-up.md
Impact: docs/contracts/DRA-148/impact.md
Status: done
Linear: DRA-152

## Read in the contract
- systems/level-up/view.md: Diagram, Interface, Presentation, The banner on the play area, The bump, Cost, What the views never do
- systems/level-up/rationale.md: Everything is drawn from images made once, Draw order

## Builds
- `game/ui/level_up_view.py` (new): `LevelUpFonts`, `LevelUpView` with `__init__`, `draw_banner` and `bump_offset`. `draw_flight` is task DRA-148-06; leave it out or as a stub that draws nothing

## Depends on
DRA-148-01, DRA-148-03, DRA-148-05

## Not in the contract
None.

## Acceptance check
From `game/`, a headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report builds the view from starting values of your own that satisfy the schema, with the game's real fonts, and then:
- draws the banner for a level (say 3) on a 640 x 480 field at the ages that show each moment (opening, falling, landing, a few ticks after it, label and pips fading in, the glint, hold, the flight start, closed) and saves the PNGs outside the repo; for each lists what is visible;
- draws a drifter stand-in and a ship stand-in over the field after the banner at the hold age, and shows their pixels are untouched by the glass or the number;
- shows no fuchsia pixel (a solid fuchsia of the HUD palette's `ship_lines`) in any frame;
- times, for 200 draws each at the age of full band height, with the glass at the starting alpha and at 0: the time per draw of `draw_banner`, and says which glass method it chose and the timings of the others it tried;
- counts surfaces: after `__init__`, 1000 draws across every age build no surface, render no text and call no scale or rotate (patch or count them), and every draw for None returns at once.
`game/tests/check.sh lint` and `typecheck` pass.

## Out of scope
- The number's flight and the HUD pop (tasks DRA-148-06 and -05). The curves (task DRA-148-03). The draw order, the bump's scroll and every `game/app/` change (the Integration Engineer's). Tests, the tuning file.
- Any sound, any blur glow, any fuchsia.
