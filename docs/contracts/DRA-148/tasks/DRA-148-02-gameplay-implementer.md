Feature: DRA-148
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/level-up.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-148/impact.md
Status: open
Linear: DRA-150

## Read in the contract
- level-up.md: `systems/level-up/core.md`: Diagram, Interface (the `core/run.py` block), Rules (The banner, Pause, Game over and a new run, The shown level, The `level_up` cue, Logging)
- run.md: Interface, "DRA-148: the level-up banner"; Rules, step 9b, The last life, A last-life tick, A game-over tick, `next_run`

## Builds
- `game/core/run.py` (changed): the `level_up` field, the two properties, step 9b on the playing and the last-life tick

## Depends on
DRA-148-01

## Not in the contract
None.

## Acceptance check
A headless script (in the implementation report) starts a run with waves and level-up rules of your choosing, plays it to a level rise and prints, per tick from the rise: `level`, `hud_level`, `level_up` (None or its age), `level_up_cue`. It shows: the banner at age 0 on the state after the rise tick with the cue True on that state only, `hud_level` the old level until the arrival tick and the new one from it, the banner None once it has lived its lifetime. Then, in a second run, the last life lost during the banner: the banner None at once, `hud_level` equal to `level`, and no banner on the later last-life ticks even if the level rises; and `next_run` giving a run with no banner. `game/tests/check.sh lint` and `typecheck` pass and `core` has no failure `impact.md` doesn't expect.

## Out of scope
- The wave clock and `core/level_up.py` (task DRA-148-01). Any view, the HUD, `game/app/`, the tuning file. Tests.
- Any sound, and any change to `core/game_flow.py`.
