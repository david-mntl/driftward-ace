Feature: DRA-56
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Status: open
Linear: DRA-60

## Read in the contract
- drifters.md: Interface, `game/core/drifters/base.py` (`drawn_parts`, `is_partly_on_screen`, `mark_entered`, `is_off_screen`, `warning_center`, `warning_tilt_degrees`, `warning_copy`, `brightness`) and `game/core/drifters/fireball.py`.
- drifters.md: Rules, The base: Drawn parts, Entering, Leaving, Warning place, Re-hit cooldown, Birth, Start.
- drifters.md: Rules, Fireball (all of it). Rules, Spawner (steps 4, 7 and 8).
- drifters.md: Diagram: the start table and the Fireball timeline.
- run.md: Rules, steps 3 (update and `mark_entered`), 7 (Hit), 8 (the re-hit cooldown) and 9 (Drop); Logging (the `drifter` lines).

## Builds
- `game/tests/core/test_fireball.py` (new)
- `game/tests/CONTEXT.md` (changed: one line for `test_fireball.py`, in the style of the `test_chain_lightning.py` line)

## Depends on
DRA-56-01

## Not in the contract
- Like `test_chain_lightning.py`, the file builds its own `DrifterTuning` for the fireball (and the meteorite, for the footprint case) from the GDD values at the top of the file, repeats its own `place`, `advance` and `active` helpers, reads no `game/tuning/` file and imports no expected number from the code under test. Source: tests/CONTEXT.md, Rules.

## Test
- Each entry starts where the start table says, with and without `invert`: no x and no y (the corner), x alone (along the top), y alone (a side), both. Rules: Fireball (Start).
- Its warning shows where the start table says for each entry. Rules: Fireball (Warning place); The base (Warning place).
- It flies in a straight line at the angle from straight down, at its speed along the path, mirrored by `invert`; Level 8 speeds it up by the hazard speed ×, the angle never changes; a placement's `speed` replaces the Level 1 speed along the path. Rules: Fireball (Born, Update, Speed at Level 1); Spawner (step 4).
- Its hitbox is the head on its center and the tail touching it from behind along its path, for both variants, mirrored with `invert`. Rules: Fireball (Hitbox).
- Its drawn parts are one box per circle, each the circle's radius plus the margin. A meteorite's drawn parts are its footprint alone. Rules: The base (Drawn parts); Fireball (Drawn parts).
- It is not removed while the tail's drawn box is still on screen, even after the head's is fully off; it is removed once both are fully past a side or the floor, each by its own edge; never at the top; never before it has entered. The corner timeline's states 258, 261 and 262 hold. Rules: The base (Leaving, Entering); Fireball (Leaving); Diagram (Fireball timeline).
- Its warning copy is tilted along its path with the tail back: the tilt's sign follows `invert`, and the copy is the comet laid straight down, sized on head plus tail, in WARNING. Rules: Fireball (Warning tilt, Warning copy).
- It refuses a specialty, and a tuning without its type values. Rules: Fireball (Born).
- In the run: a fireball touching the ship is a hit and costs a life; it keeps flying, dims, and can't hit again during its re-hit cooldown even if the ship still touches it; touching the tail alone is a hit; it is dropped and logs `drifter gone` only once head and tail are both off. Rules: Fireball (Touch, Hitting again, Leaving); The base (Re-hit cooldown); run.md, Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_fireball.py` in the `core` step.

## Out of scope
- The ship against every fireball variant from its file (task DRA-56-03).
- The fireball view and warning pixels (checked by task DRA-56-02 and at integration).
- Graze scoring. Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
