Feature: DRA-47
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-54

## Read in the contract
- Interface, `game/core/collision.py`; Rules, Collision (all of it: Line, grow_hitbox and Unknown shape kind included).
- Interface, `game/core/drifters/chain_lightning.py`: `ChainLayout`, `InvertMirror`, `ChainLightningVariantExtra`, `ChainLightningTypeExtra`, `layout_size`, `chain_hitbox`, and the `ChainLightning` methods `is_charging`, `is_firing`, `current_hitbox`.
- Rules, Chain lightning: Layout, Born, Cycle, On screen, Firing arcs, Hitbox. Rules, Tuning files: The chain lightning's file.
- Rules, The base: Phase and Hitbox. Rules, Spawner (to build drifters).

## Builds
- `game/tests/core/test_collision.py` (changed: line tables, the guard and helpers for three kinds, and a chain lightning branch in the ship-against-every-variant cases; the existing tables, invariants and the two ship tests at the end stay)
- `game/tests/CONTEXT.md` (changed: the `test_collision.py` line names the line tables and the chain lightning branch)

## Depends on
DRA-47-01, DRA-47-03

## Not in the contract
- The chain lightning's ship cases read `game/tuning/drifters/chain_lightning.json` with `json`, as the other ship cases read their files (tests/CONTEXT.md allows numbers from `game/tuning/`), and build `ChainLayout`, the two extras and `VariantTuning` with the contract's `layout_size` and `chain_hitbox`. They never import `app`. The file is content, filled by whoever the Director names; if it is missing, report it.
- Structure kept from DRA-39 (scope report DRA-39, Decision log; scope report DRA-47, Limits: "every pair of shape kinds, both ways round, and the ship against every chain lightning variant, firing and charging").

## Test
- Three new tables: line and line, circle and line, box and line. Each case is checked both ways round with the same result. Rules: Collision (Line; strict overlap; the result never depends on the order).
- Each new table holds exact-number edge cases: side touch (no), a hair inside (yes), round-end touch on the line's axis and at a 3-4-5 angle (no), a hair inside those (yes), crossing (yes), parallel edges touching (no), one shape inside the other (yes), identical (yes), far apart (no). For box and line also a line through the box with both ends outside (yes) and a round end touching a box corner (no). A line whose two ends are the same point behaves as a circle of radius thickness / 2. Rules: Collision (Line).
- The existing invariants cover the line cases too: moving both sides by the same offset, an empty hitbox, adding a shape, growing either side. `grow_hitbox` on a line adds twice the margin to its thickness and leaves its ends where they were. Rules: Collision (grow_hitbox, Line).
- Guard: the shape kinds the tables cover equal the kinds in `core.collision.Shape`, now three, and every unordered pair of the three has a table. Rules: Collision (Unknown shape kind).
- Unknown shape kinds still raise `TypeError` from all three functions, with a line on the other side too. Rules: Collision (Unknown shape kind).
- Ship against every chain lightning variant, with and without `invert`, from its tuning file: made ACTIVE and moved to a firing state with every node on screen, it overlaps `ship_hitbox(spawn())` when the middle of any one arc sits on the ship's center, and when any one node does; placed so that its nearest firing shape is clear of the ship by its own numbers (half the arc width, or the node radius, plus the ship's half size, on an axis), it doesn't. At the same places it never overlaps while charging or in WARNING. No test code names a variant: a new layout is covered by its entry in the file alone. Rules: Chain lightning (Layout, Cycle, Hitbox); The base (Phase, Hitbox).
- The meteorite and satellite ship cases keep working from their files; a drifter type with no tuning file still fails the test, naming the type. Rules: Tuning files.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs the line tables and one chain lightning ship case per variant and `invert` value in `game/tuning/drifters/chain_lightning.json`.

## Out of scope
- The chain lightning's cycle, rays, warning, scaling and its life in the run (task DRA-47-08).
- The polygon shape (scope report DRA-47, Out). Graze scoring.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
