Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-104/tasks/DRA-104-06-qa-engineer.md` (the seed and the UFO in the wave files), started by the Director's session.
2. **Delivered:** `game/tests/core/test_wave_files.py` (changed), `game/tests/CONTEXT.md` (the `test_wave_files.py` entry and the planet entry's unknown-type note brought up to date).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`; `test_wave_files.py` has 217 tests, all passing, in the `core` step (3132 core tests in all). Covered, one per behavior of the task's `## Test` list:
   - Unknown type: names `comet`, `Meteorite`, `UFO` and empty are refused; the message lists the types in enum order ending `planet, ufo)`; `ufo` itself loads.
   - Seed range: 0, 1, 7, 2^31, MAX_SEED - 1 and 4294967295 are accepted and kept; -1, 4294967296, 2^64, 1.5, -0.5, True, False, "5", None, a list and an object are refused with `placements[n].seed must be an integer from 0 to 4294967295`.
   - Default seed: a UFO with none gets `placement_seed(<wave id>, <file index>)` with the index taken before the sort by `at_px`; another wave id gives another seed; a given seed is kept; every other drifter (and the whole good set) keeps None.
   - Load-time refusals naming the placement: a seed on a meteorite, satellite and coin (`<type> has no seed`, cause kept); a UFO at y 0, 100, 187.5, 187.99, 440.01, 440.5, 480 (`ufo placement y <y> is outside its band 188 to 440`); y 188 and 440 load.
   - One path per UFO: the later placement by file order (not trigger order) is named with the earlier; three sharing a seed name the first; a given seed equal to another UFO's default seed, in both orders, is refused; the same seed in two waves loads.
   - Seam: a UFO below 120 px (0, 50, 100, 119.5, 119.99) is refused `a hazard (ufo) at <n> px is inside the first 120 px`; 120, 120.5 and 600 load.
   The UFO goes in by an edit that sets a wave's whole `placements` list, so the good set files are unchanged.
4. **Assumptions:** `make_tuning` now also builds the UFO's records from the GDD guess values (disc 40 x 10, dome 9, speed_ratio 0.3, band 188 to 440, as `test_ufo.py` does). The seed limit 4294967295 is written in the test from waves.md, not imported. A float seed is tested as 1.5 and -0.5 only; waves.md says "an integer", and a whole float such as 5.0 is not tested because the contract does not say it.
5. **Documentation differences:** None.
6. **Next:** the Integration Engineer, or close-out of DRA-104-06. No bug found: the loader (`game/core/wave_files.py`) did what the contract says on every case.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
