Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the implementation of DRA-76-03 (`game/core/waves.py`), asked by the `/implement` skill, against `docs/contracts/systems/waves.md`.
2. **Delivered:** this report, `docs/reports/review/DRA-76-03-gameplay-implementer.md`. Reviewed: `game/core/waves.py`.
3. **Checks:** by reading only, nothing run.
   - Interface: every constant, class, field, property and function in `waves.py` matches the contract's Interface by name, order and type. Two extra module constants (F1).
   - Clock: I walked the acceptance script's first line by hand (Wave 0 due at tick 3, `a` due at tick 7, 2-tick rest after `a`, `p` the only Level 1 pick, rise to Level 2 when `p` ends). It matches `w0/1/0 ... q/2/0`.
   - Rules traced: rest countdown and start at the ending tick's distance, `into` rounded to `DISTANCE_DECIMALS`, due prefix from `spawned`, level rise before the rest gap, contiguous start with no rest, Level 8 random picks past the playlist, seeds only from `random.Random(seed)`, log order `wave end`, `level up`, `rest start` or `wave start`.
   - Imports are stdlib, `core.levels`, `core.scroll`, `core.drifters.spawner` only. No pygame, no sleep or thread, no module-level `random.*`, no audio.
   - I did not run `ruff`, `check.sh` or the acceptance command. The report's claims are ones the code can pass.
4. **Assumptions:** none beyond the implementer's three, which I accept (extra constants, `ValueError` from `check_level` in `level_slots` and `pool_ids`, placements sorted).
5. **Documentation differences:** None.
6. **Next:** QA Engineer, with this report. No finding asks for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-76-03-F1 | note | game/core/waves.py:30 | no action |

### DRA-76-03-F1
`SEED_BITS` (line 30) and `REST_GAP_DECIMALS` (line 35) are module constants the contract's Interface does not list. Both are `Final`, documented, and carry values the contract gives (`getrandbits(64)`, `round(..., 6)`). They avoid magic numbers (tech rule: every number traced). The implementer disclosed them in Assumptions. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- Rest gap: a wave with `extra_rest_ticks` 2 shows `rest` on exactly 2 states, and the next wave starts at the distance of the tick the rest ends.
- A wave that ends partway through a tick's scroll with no rest: the next wave starts at old start plus length, and a trigger at 0 in the next wave is due on that same tick (`spawns_due` holds both waves' placements, in order).
- Level rise: the level is 2 in the state of the tick the Level 1 playlist's last wave ends. Empty playlists are skipped with one `level up` line. At Level 8 the level stays 8 and random picks continue forever.
- Picker: with two or more pool waves it never repeats the last wave, including across a level change and after Wave 0. With one it repeats. Same seed gives the same sequence; `next_run_waves` gives a new `run_seed`.
- A placement with `at_px` beyond the wave's length is never due; a placement exactly at the end is due on the ending tick.
