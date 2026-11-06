Feature: DRA-148
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/level-up.md, docs/contracts/systems/hud.md
Impact: docs/contracts/DRA-148/impact.md
Status: done
Linear: DRA-153

## Read in the contract
- systems/level-up/view.md: Interface, LevelSlot, level_slot, Presentation, The HUD pop, Cost, What the views never do
- systems/level-up/core.md: Interface, shown_level, The shown level
- hud.md: Presentation, Rules, The level pop, The level bars, Rationale, A class, All motion is frames made ahead of time

## Builds
- `game/ui/hud.py` (changed): `LevelSlot`, the optional look and banner arguments, the shown level, the pop (number, new climb bar, box outline) and `level_slot`

## Depends on
DRA-148-01, DRA-148-03

## Not in the contract
None.

## Acceptance check
From `game/`, a headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report builds the HUD twice, with the game's `hud.json` rules and art: once the old way and once with a look of your own that satisfies the schema, then:
- draws the HUD with a banner of your own at ages before, on and after the arrival tick and in the middle of the pop, with the previous level 2 and the level 3, and saves the level box's crop for each: the old level (number and bars) before arrival, the new one from it, larger than normal on the arrival frame and back to normal size by the pop's end, with the new climb bar and the box outline flashing and then back to normal;
- shows the HUD drawn with no banner, or with the old-style construction, is pixel-equal to what it drew before this task (compare against the old construction on the same run);
- shows `level_slot(level)`'s center lies inside the level box for every level, and its size is the number image's;
- counts surfaces: after `__init__`, 500 draws across the pop build no surface and render no text beyond what the HUD already did.
`game/tests/check.sh lint`, `typecheck` and `ui` pass: the existing HUD tests are not changed.

## Out of scope
- The banner on the play area and the flight (tasks DRA-148-04 and -06). The curves (task DRA-148-03). The panel art and `tools/art/hud_panel.py`, `hud.json`, every other HUD element. `game/app/`. Tests.
