Verdict: pass
Created by: qa-engineer

1. **Task:** QA test task `docs/contracts/DRA-86/tasks/DRA-86-07-qa-engineer.md`, started by /implement: the polygon tables, the push-out tests and the island ship cases in `core/test_collision.py`.
2. **Delivered:**
   - `game/tests/core/test_collision.py` (changed): `moved` and `anchor` take a `Polygon`; four new tables in `TABLES` (polygon with polygon, box, circle and line); the guard expects `{Circle, Box, Line, Polygon}`; the unknown-kind test also puts a polygon next to the bad shape; new tests for the triangle's touches, the other point order, the grown polygon, `deeply_overlaps`, `exit_distance` (four tests), `push_directions` (two tests), the push-out `TypeError`, and the island (ship at its touching distance, the spawned state, BLOCK and no graze zone); the loader has an island branch (`load_island_cases`, `ISLAND_CASES`).
   - `game/tests/CONTEXT.md` (changed: the `core/test_collision.py` paragraph).
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui PASS. `core`: 2672 passed, 3 failed. Every `test_collision.py` test passes (2323). The 3 failures are all in `test_wave_files.py` (the unknown-type refusal prefix lacks `floating_island`), the one failure the task's Acceptance check names as left until DRA-86-09. See B1.
   - `test_drifter_registry.py` passes. `typecheck` passes with the new tests in it.
   - Not vacuous: 18 mutations of `game/core/collision.py` and `floating_island.py`, run on a copy under the scratchpad (never the repo), were all caught: touching counted as overlap, raw normals in the depth, grow line not doubled, no inward normal, moving polygons before solid ones, point order ignored (area sign), no chaining in `exit_distance`, polygon-circle and polygon-line branches, tolerance 0, no `TypeError` on the solid side, the grown polygon dropping itself, BLOCK to HIT, the invert dropped from the triangle and the T, the island born in WARNING.
   - Every expected number is whole, a half, a sixteenth or a 3-4-5 triangle, or comes from `game/tuning/drifters/floating_island.json`. The island shapes are written from the contract's Diagram, not read back from `island_hitbox`.
4. **Assumptions:**
   - `SURFACE_TOLERANCE` is not exactly reachable in floating point, so "no deeper than" is tested at half the tolerance and "just deeper" at twice it. A slope step of 1x tolerance is 0.6x deep (counts as touching) and 2x is 1.2x (deep): that also catches a depth measured on a normal not made unit.
   - "Each outer side" for the box islands: each box of the island is put on the ship's center line in turn (an L's upright met from the left needs the island's center to the right of the ship, a negative distance). The triangle has four sides: right of the ship (straight side), left (the tip), and above or below (the flat side, and the slope).
   - A rectangle has no `invert`, so its case is built once; the L, the T and the triangle twice (the contract, Born, and 05-floating-islands rule 9).
   - Task 07 does not ask for a test that the spawner refuses `invert` on a rectangle, so there is none.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, task `DRA-86-09-qa-engineer.md` (it fixes the type list in `test_wave_files.py`, contract Impact). After that `check.sh` should end `QA: pass`. The Integration Engineer waits for DRA-86-08 and DRA-86-09.
7. **Status:** done.

## Bugs
- **B1** `game/tests/core/test_wave_files.py`, owner: QA Engineer (task DRA-86-09, not a game code bug). Reproduce: `game/tests/check.sh core -k wave_files`. Expected: the unknown-type refusal lists the types in enum order, `(meteorite, satellite, chain_lightning, fireball, coin, floating_island)`. Actual: the three `placement type 'ufo'`, `'Meteorite'` and `''` rows still expect the list without `floating_island`; the code now reports it. Source: drifters.md, Impact table (the `test_wave_files.py` row); waves.md, The wave files (Drifter type: the type list in enum order). Proposed fix: update those three `Refusal` prefixes in DRA-86-09. This is the failure the Acceptance check of DRA-86-07 says stays open until that task. Not fixed here: the task forbids editing other test files.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3 failed in `test_wave_files.py`, 2672 passed) · ui PASS
QA: fail (core)

## Round 2 2026-10-21

1. **Task:** Re-test of B1 (the three `test_wave_files.py` unknown-type rows), fixed by task DRA-86-09. DRA-86-03 B1 is a known issue accepted by the Director and is not re-opened.
2. **Delivered:** this round in `docs/reports/qa/DRA-86-07-qa-engineer.md`. No test or game file changed in this round.
3. **Checks:**
   - B1 reproduce `game/tests/check.sh core -k wave_files`: 177 passed. The three `placement type 'ufo'`, `'Meteorite'`, `''` rows now expect `(meteorite, satellite, chain_lightning, fireball, coin, floating_island)` (`test_wave_files.py:359`), the enum order the code reports.
   - Neighbor: `game/tests/check.sh core -k collision` passes (the 2323 DRA-86-07 cases).
   - Full `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS, ends `QA: pass`.
   - Acceptance check of DRA-86-07 (the collision tables, push-out tests and island ship cases pass against the code, with `check.sh` ending `QA: pass`): shown by the two runs above.
4. **Assumptions:** None.
5. **Documentation differences:** pending Director approval, minor. `docs/contracts/systems/waves.md:299` (The wave files, Drifter type) still shows the example message with the list `(meteorite, satellite, chain_lightning, fireball, coin)`. Its own text says "the list in enum order", and `drifters.md` (Impact table, `test_wave_files.py` row) says the list gains `floating_island`. Proposed change: add `, floating_island` to the example list in `waves.md:299`. The code and the tests already follow the enum.
6. **Next:** Integration Engineer, once the other DRA-86 QA re-tests are clear. The Architect and the Director may fix the `waves.md` example.
7. **Status:** done.

## Bugs
- **B1** fixed. `test_wave_files.py` now expects `floating_island` last in the unknown-type list. No open bug.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
