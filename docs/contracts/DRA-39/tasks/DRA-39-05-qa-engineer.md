Feature: DRA-39
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-44

## Read in the contract
- Interface, `game/core/collision.py`; Rules, Collision (all of it, Unknown shape kind included).
- Rules, The base: Phase and Hitbox. Rules, Spawner (to build drifters). Rules, Meteorite and Satellite: Variants.
- Rules, Tuning files (where each drifter's variants live and which schema each file follows).

## Builds
- `game/tests/core/test_collision.py` (changed: rebuilt to the structure below; the two ship tests at its end stay as they are)

## Depends on
DRA-39-01, DRA-39-03

## Not in the contract
- The ship-against-every-variant cases read `game/tuning/drifters/*.json` directly with `json` (tests/CONTEXT.md allows numbers from `game/tuning/`) and build the tuning records themselves, including `SatelliteVariantExtra` from `angle_degrees`. They never import `app`. `satellite.json` is content, filled by whoever the Director names; if it is missing, report it.
- Structure proposed by the architect in Advice mode and accepted by the Director (scope report DRA-39, Decision log and Limits).

## Test
- Each pair of shape kinds (circle and circle, box and box, circle and box) has its own table of cases, and every case is checked both ways round with the same result. Rules: Collision (strict overlap; the result never depends on the order).
- Each table holds exact-number edge cases: an exact edge touch (no overlap), a hair inside it (overlap), an exact corner touch (no), a corner a hair inside (overlap), one shape inside the other (overlap), identical shapes (overlap), far apart (no), with numbers exact in binary (whole numbers, halves, 3-4-5 triangles). Rules: Collision.
- Invariants over every table case: moving both hitboxes by the same offset with `place_hitbox` (negative, fractional and screen-sized offsets) never changes the result; an empty hitbox overlaps nothing; adding a shape to either side never turns an overlap into none; growing either side with `grow_hitbox` never turns an overlap into none. Rules: Collision (any shape; grow_hitbox).
- Guard: the shape kinds the tables cover equal the kinds in `core.collision.Shape` (from `typing.get_args`), and every unordered pair of kinds has a table, so a new shape kind fails this test until its tables exist. Rules: Collision (Unknown shape kind).
- An object that is not a known shape kind raises `TypeError` from `hitboxes_overlap` (on either side), `place_hitbox` and `grow_hitbox`. Rules: Collision (Unknown shape kind).
- Ship against every variant: for every `DrifterType` and every variant in its tuning file, spawned with `spawn_drifter` and made ACTIVE, placed against `ship_hitbox(spawn())` from the left, the right, above and below along the ship's center lines: no overlap at the exact touching distance, overlap 0.5 px closer, overlap centered on the ship, and never any overlap in WARNING. The touching distance comes from the shapes' own numbers in the file (edge sums for boxes, radius plus half-size for a circle met on an axis), never from `core.collision`. No test code names a drifter type or a variant: a new drifter or variant is covered by its file alone. Rules: Collision; The base (Phase, Hitbox); Meteorite and Satellite (Variants).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs the rebuilt tests in `tests/core/test_collision.py`, including one ship case per drifter type and variant in `game/tuning/drifters/`.

## Out of scope
- Graze zones, spawner rules and drifter movement (task DRA-39-06). Hits in the run (task DRA-39-07).
- Line and polygon shapes (later features add their tables).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
