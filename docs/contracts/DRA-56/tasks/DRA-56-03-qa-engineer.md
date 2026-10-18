Feature: DRA-56
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-59

## Read in the contract
- Interface, `game/core/drifters/fireball.py`: `FireballTypeExtra`, `fireball_hitbox`.
- Rules, Fireball: Variants, Hitbox, Born, Start. Rules, Tuning files: The fireball's file.
- Rules, Collision (circle and box). Rules, The base: Phase and Hitbox. Rules, Spawner (to build drifters).

## Builds
- `game/tests/core/test_collision.py` (changed: a fireball branch in the ship-against-every-variant cases; the existing tables, the chain lightning branch and the other ship tests stay)
- `game/tests/CONTEXT.md` (changed: the `test_collision.py` line names the fireball branch)

## Depends on
DRA-56-01

## Not in the contract
- The fireball's ship cases read `game/tuning/drifters/fireball.json` with `json`, as the other ship cases read their files (tests/CONTEXT.md allows numbers from `game/tuning/`), and build `FireballTypeExtra` and `VariantTuning` with the contract's `fireball_hitbox`. They never import `app`. The file is content, filled by whoever the Director names; if it is missing, report it.
- Structure kept from DRA-39 and DRA-47 (scope report DRA-56, Limits: "Collision tests in the DRA-39 structure: the ship against every fireball variant").

## Test
- Ship against every fireball variant, with and without `invert`, from its tuning file: one case per variant and `invert` value. Its hitbox is `fireball_hitbox` of the file's values, and the case meets the ship at its own touching distance from each side, as the other shape cases do: just clear of it, no overlap; 0.5 px inside, overlap. Rules: Fireball (Hitbox); Collision.
- The same cases never overlap in WARNING and do once ACTIVE on the ship's center. Rules: The base (Phase, Hitbox).
- The tail alone touches: placed so only its tail circle reaches the ship (its center 0.5 px inside the ship's nearest edge on an axis, the head clear), it overlaps; moved just clear, it doesn't. No test code names a variant: a new size is covered by its entry in the file alone. Rules: Fireball (Hitbox, Touch).
- The meteorite, satellite and chain lightning ship cases keep working from their files; a drifter type with no tuning file still fails the test, naming the type. Rules: Tuning files.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs one fireball ship case per variant and `invert` value in `game/tuning/drifters/fireball.json`.

## Out of scope
- The fireball's start, flight, leaving, warning and life in the run (task DRA-56-04).
- Graze scoring. Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
