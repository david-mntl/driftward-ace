Feature: DRA-96
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-102

## Read in the contract
- Diagram: Planet (the sketch: the body, its hitbox, the field).
- Interface: `game/core/drifters/planet.py` (`PlanetVariantExtra`, `PlanetTypeExtra`, `planet_hitbox`, `Planet`).
- Rules: Planet (Variants; Hitbox; Touch); Tuning files (the planet's file: what `app.tuning` builds); How to add a drifter (the branch in the ship-against-every-variant tests).
- Impact, the DRA-96 table (the `test_collision.py` row).

## Builds
- `game/tests/core/test_collision.py` (changed: a planet branch in `load_variant_cases`, and the tests below)
- `game/tests/CONTEXT.md` (changed: the planet in the `test_collision.py` paragraph)

## Depends on
DRA-96-02

## Not in the contract
- The cases read `game/tuning/drifters/planet.json` like every other drifter's, so the file must exist before this task runs. It is content, filled to `docs/contracts/schemas/planet-tuning.schema.json` by whoever the Director names. Source: drifters.md, Purpose (Who builds what) and Impact.

## Test
- The planet's file gets its own branch in `load_variant_cases`: one case per variant, built the way `app.tuning` builds it (`planet_hitbox`, `PlanetVariantExtra`, `PlanetTypeExtra`, `speed_ratio` 0.0, `entry_warning_ticks` from the file), with the expected circle written in the test from the file's `size` (radius `size / 2`), never taken from `planet_hitbox`, and the spawned planet's hitbox must equal it. Rules: Tuning files (the planet's file); Planet (Hitbox).
- Each planet case goes through the touching-distance test of the plain-hitbox types: no overlap in WARNING, overlap in ACTIVE with the circle on the ship's center, each side just clear (no overlap) and 0.5 px inside (overlap). Rules: Planet (Touch); How to add a drifter.
- The field never counts: with the ship inside `pull_radius` and just clear of the body, the planet's hitbox doesn't overlap the ship, and `effect_on_touch()` is `HIT`. Rules: Planet (Hitbox; Touch).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once the Impact table's expected failures are cleared, with the planet's cases in `test_collision.py` in the `core` step and all of them passing.

## Out of scope
- The planet's own rules, the pull, planets in the run (tasks DRA-96-05 and DRA-96-07).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
