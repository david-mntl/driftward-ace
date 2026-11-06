Feature: DRA-148
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/level-up.md
Impact: docs/contracts/DRA-148/impact.md
Status: open
Linear: DRA-151

## Read in the contract
- level-up.md: `systems/level-up/view.md`: Interface (`ui/level_up_rules.py` and `ui/level_up_motion.py` blocks); Presentation (the paragraphs for the glass, the number, the bump, the flight and the HUD pop, for what each curve drives)
- level-up.md: `docs/contracts/schemas/level-up.schema.json`, whose sections the look records mirror

## Builds
- `game/ui/level_up_rules.py` (new)
- `game/ui/level_up_motion.py` (new)

## Depends on
None

## Not in the contract
- Easing curves: the contract says "eased" and names the end points. Pick any smooth curve that meets the end points and the monotone parts it names (a smoothstep or a cubic ease-out); say which in the docstring. Source: architect call, FYI.

## Acceptance check
A script (in the implementation report), run with starting values of your own that satisfy the schema, prints each function of `ui/level_up_motion.py` at the ticks that matter (before the start, the start, the middle, the end, after the end) and shows: `band_shares` 0 before opening, 1 while open, 0 after closing, the glass closing before the lines; `fall_offset` negative up to the fall start, past the place by the overshoot at its peak, exactly 0 on the landing and after; `pose_scales` stretched while falling, squashed on landing, (1, 1) after the squash; `bump_offset` 0 before landing and from the end of the bump on, the bump's pixels at its peak, never negative, and 0 always when the bump is 0 px; `fly_position` exactly the start at share 0 and exactly the end at share 1; `pop_scale` the start scale at 0 and exactly 1.0 from the pop's end on. `game/tests/check.sh lint` and `typecheck` pass.

## Out of scope
- Any drawing, any pygame import, the view (tasks DRA-148-04 and -06) and the HUD (task DRA-148-05). The tuning file and its loader, `game/app/`. Tests.

