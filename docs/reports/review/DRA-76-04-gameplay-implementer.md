Status: reviewed
Created by: implementation-reviewer

1. **Task:** review `game/core/wave_files.py` (task DRA-76-04, `build_wave_book`) against `docs/contracts/systems/waves.md`, the pillars, the tech rules and the implementer's Decisions. Asked by the `/implement` skill.
2. **Delivered:** this report, `docs/reports/review/DRA-76-04-gameplay-implementer.md`.
3. **Checks:** read only, nothing run. Compared every Rules line of "The wave files" with the code: error wording, check order, field lists, bool exclusion, the seam test, the pool checks, the sort and the built shapes. Compared the Acceptance check's five lines with the code path for each; they match. Read `core/drifters/spawner.py` (`Placement`, `spawn_drifter`) and `core/waves.py` (shapes and `pool_ids`) for the call sites. Decisions match the code.
4. **Assumptions:** the contract's Interface fixes only the public function and four constants. I took the private helpers as the implementer's own design.
5. **Documentation differences:** None that break a contract or a locked decision. One small gap in the contract's import list is in F3 (a note).
6. **Next:** Gameplay Implementer, Review fix mode, for F1. Open: 0 must-fix, 1 should-fix, 4 note.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-76-04-F1 | should-fix | game/core/wave_files.py:116 | fixed |
| DRA-76-04-F2 | note | game/core/wave_files.py:25 | no action |
| DRA-76-04-F3 | note | game/core/wave_files.py:12-17 | no action |
| DRA-76-04-F4 | note | game/core/wave_files.py:282 | no action |
| DRA-76-04-F5 | note | game/core/wave_files.py:187 | no action |

### DRA-76-04-F1
`_is_number` calls `math.isfinite(value)` on an `int`. A JSON integer too large for a float (a few hundred digits, for example `"length_px": 1000...0`) makes `math.isfinite` raise `OverflowError`. The same holds for `float(at_px)` and `float(length_px)` at lines 204 and 248 if a huge int got past. Python's decoder accepts such an int, so the file would crash the loader with an `OverflowError` that does not name the file or the field.
Rule: `build_wave_book` raises a `ValueError` naming the file and the problem for every bad input (waves.md, Rules, The wave files; game/CONTEXT.md, Error handling).
Change: make `_is_number` refuse a value that cannot become a finite float (for example, catch `OverflowError` and return False), so it reports "must be a number ...". An int too large for a float is not a usable px value.

### DRA-76-04-F2
`log = logging.getLogger(__name__)` at line 25 is never used. The contract lists `logging` in the Imports and says this module logs nothing, so the line follows the contract. Change: none.

### DRA-76-04-F3
The code also imports `dataclasses` and `math`; the contract's Imports line lists `collections.abc, logging, re, typing`. Both are stdlib and neither touches pygame, ui or app, so no rule is broken. The Architect may add them to the list. Change: none.

### DRA-76-04-F4
The string `f"{WAVES_FOLDER}/{PLAYLIST_NAME}.json"` is built in three places (lines 282, 313, 330). A small duplicate. Change: none.

### DRA-76-04-F5
A wave file named `playlist` is not refused. The Rationale says `playlist` can't be a wave id, but no Rules line lists a check for it, and the implementer states it in Assumptions. Change: none. The Architect may decide whether to add the check.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. Every number traces to the GDD or tuning: pass
7. pass
8. Smells: F2, F4
9. pass
10. pass

## For QA
- A hazard at `at_px` 119.9, exactly 120 and 0: refused, accepted, refused. A coin at 0 is accepted.
- A huge integer in `length_px` or `at_px` (for example 400 digits): it must give a `ValueError` naming the file (F1).
- `true` for `length_px`, `at_px`, `min_level` or `random_count`; `NaN` and `Infinity` in a number field: each refused.
- Wave files with ties in `at_px`: file order kept. Same inputs twice: the same book and the same first error.
- A pool wave with `min_level` 8 and a playlist that asks for a random pick at Level 1: refused with the "no pool wave with min_level <= 1" message.

## Re-check 2026-10-19

1. **Task:** re-check review finding F1 on `game/core/wave_files.py` after the implementer's Review fix (asked by the `/implement` skill).
2. **Delivered:** this appended section in `docs/reports/review/DRA-76-04-gameplay-implementer.md`.
3. **Checks:** read only, nothing run. Read `_is_number` at `game/core/wave_files.py:114-124` and every `float(...)` call (lines 212, 256). Every float conversion of a user number sits behind `_is_number`, so a huge int can no longer reach it. The integer predicates never convert to float, so they are not affected.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, with this report. Open: 0 must-fix, 0 should-fix, 0 notes needing a change (4 notes at `no action`). Round 2 fixes only open must-fix and should-fix; none are open, so the task goes to QA.
7. **Status:** done.

- DRA-76-04-F1: fixed. `game/core/wave_files.py:121-124` catches `OverflowError` from `math.isfinite` and returns False, so a huge int gets the "must be a number ..." message naming the file and field.
- DRA-76-04-F2 to F5: notes at `no action`, unchanged.
