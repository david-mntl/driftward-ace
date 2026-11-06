Feature: DRA-148
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/level-up.md, docs/contracts/systems/hud.md
Impact: docs/contracts/DRA-148/impact.md
Status: done
Linear: DRA-157

## Read in the contract
- systems/level-up/view.md: Interface, Presentation, The bump, The HUD pop, What the views never do
- systems/level-up/core.md: Rules, The shown level
- hud.md: Rules, The level pop, The level bars

## Builds
- `game/tests/ui/test_level_up_motion.py` (new)
- `game/tests/ui/test_hud_level_up.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for each new file)

## Depends on
DRA-148-03, DRA-148-05

## Not in the contract
- Like `test_hud.py`, the HUD tests build the HUD from the game's `hud.json` and art, and a look built at the top of the file that satisfies the schema. They read no `level_up.json`. Source: tests/CONTEXT.md, Rules.

## Test
- `bump_offset` is 0 before the landing and from the end of the bump on, never negative, reaches the bump's pixels, and is 0 always for a bump of 0 px: the picture always comes back. Rules: The bump.
- `band_shares` is 0 before opening and after closing, 1 while open, and the glass closes before the lines. Presentation: The banner on the play area (Glass, Hairlines).
- `fall_offset` is exactly 0 on the landing tick and after, and above the resting place before it. `pose_scales` is (1, 1) once the squash has settled. Presentation: The banner on the play area (The number).
- `fly_position` is exactly the start at share 0 and the end at share 1; `fly_share` is 0 up to the flight's start and 1 from the arrival tick. Presentation: The flight.
- `pop_scale` is the start scale at 0, is never above it, and is exactly 1.0 from the pop's end on. Presentation: The HUD pop.
- The HUD shows the previous level (number image and lit bars) for every banner age below the arrival, and the new level from it. Rules: The shown level; Presentation: The HUD pop.
- The HUD level number is larger than normal on the arrival frame and back to normal by the pop's end; the new climb bar and the box outline flash and then are as without a banner. Presentation: The HUD pop.
- The HUD with no banner, or built with no look, draws pixel-for-pixel what it drew before (the same run and tick, built the old way). Interface (`HudView`).
- `level_slot(level)`'s center lies inside the level box for every level 1 to 8. Interface (`LevelSlot`).
- No HUD draw during the pop builds a surface or renders text (the pop's frames are made at construction). Presentation: Cost.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_level_up_motion.py` and `test_hud_level_up.py` in the `ui` step and all their tests passing.

## Out of scope
- The banner view and the flight (tasks DRA-148-04 and -06): their look is checked by the Director and by the browser checks. The core tests (tasks DRA-148-07 and -08). The loaders in `game/app/`.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
