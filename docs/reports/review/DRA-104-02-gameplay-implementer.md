Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review task DRA-104-02 (the `seed` placement field, default seeds and the one-path-per-UFO check in the wave loader), from the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-104-02-gameplay-implementer.md`.
3. **Checks:** Read `game/core/wave_files.py` in full against `docs/contracts/systems/waves.md` (Interface for `wave_files.py`, Rules for the wave files, Impact, Rationale), `docs/contracts/systems/drifters.md` (`Placement.seed`, `MAX_SEED`, `placement_seed`, `seeded`), `game/core/drifters/spawner.py` (`_check_seed`, `placement_seed`), `docs/design/gdd/drifters/07-ufo.md` (seed, rules 10 and 12) and `game/CONTEXT.md`. Traced the task's acceptance script by hand: the seven lines the report shows match the code paths. Nothing was run.
4. **Assumptions:** The check order inside one placement is judged against the order the existing loader already used before DRA-104, not only the order the contract lists the fields in (see F1).
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Two notes, both `Change: none`. Nothing open asks for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-104-02-F1 | note | game/core/wave_files.py:258 | no action |
| DRA-104-02-F2 | note | game/core/wave_files.py:246 | no action |

### DRA-104-02-F1
`seed` is checked before `x`, `y` and `specialty`, while waves.md, Rules, The wave files ("fields in the order below") lists `seed` last. This follows the order the loader already had (`variant`, `invert`, `as_level` before `x`), and it only decides which error shows when two fields of one placement are bad. Change: none.

### DRA-104-02-F2
`_build_placement` now rebuilds the file name `f"{WAVES_FOLDER}/{wave_id}.json"` that `_build_wave` also builds (line 198). The Decisions note says so. Rule: no duplicated blocks (checklist item 8). One line, so it is a note only. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F2
9. pass
10. pass

## For QA
- A UFO with no `seed`, same wave file loaded twice: the default seed is the same both times and equals `placement_seed(<wave id>, <file index>)`, not the index after the sort by `at_px`.
- `seed` of 4294967296, 5.0, "5" and true: each refused with `placements[<i>].seed must be an integer from 0 to 4294967295`; 0 and 4294967295 load.
- The same seed on UFOs in two different waves loads; in one wave the later one by file index is named. A given seed equal to another UFO's default seed is also refused.
- A wave with both a duplicate seed and a UFO outside its band: the band error comes first (the one-path check runs after every placement is spawned).
- A seed on a meteorite: `placements[<i>]: meteorite has no seed`.
