Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-76-04-gameplay-implementer (`game/core/wave_files.py`, `build_wave_book`), Verify mode, started by the `/implement` skill. Review report is `Status: reviewed` and its Re-check says F1 is fixed.
2. **Delivered:** this report, `docs/reports/qa/DRA-76-04-gameplay-implementer.md`. No test files (Verify saves none).
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass` (46 tests).
   - Acceptance check run from `game/` as `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python < <the task's command>`. Output, the five lines the task asks for:
     ```
     ['p', 'w0'] w0 [0.0, 150.0] 0 30 ('p',)
     waves/w0.json: placements[0]: a hazard (meteorite) at 100 px is inside the first 120 px
     accepted
     waves/playlist.json: wave_zero names 'nope', which is not a wave
     waves/playlist.json: levels[0] (level 1) has random_count 1 but no pool wave with min_level <= 1
     ```
   - Seam edge: hazard at `at_px` 0, 119.9, 119.999999 refused; 120, 120.0, 121 accepted. Same for chain lightning and fireball (each variant, tuning files read: 120 accepted, 119 refused, all 15 hazard variants). A coin accepted at 0, 119.9 and 120. A satellite and a coin without the coordinate they need are refused naming the placement.
   - Review "For QA" lines: huge int (10**400) in `length_px`, `at_px`, `x`: `ValueError` naming file and field, no crash (F1 holds). `true` for `length_px`, `at_px`, `min_level`, `random_count`, `extra_rest_ticks`, `as_level`, `x`: refused. `NaN`, `Infinity`, `1e999` (decoded from JSON text) in `length_px` and `at_px`: refused. Ties in `at_px` (10, 10, 10.0): file order kept; sorted by trigger; `at_px` and `length_px` built as `float`. Pool wave `min_level` 8 with a Level 1 random slot: `levels[0] (level 1) has random_count 1 but no pool wave with min_level <= 1`. Pool wave `min_level` 8 with a random slot only at Level 8: accepted. No pool wave at Level 8 and no random slots: `waves: no pool wave can play at level 8`.
   - About 150 further refusals tried, all raise `ValueError` with the file first and the field named, none crash: unknown wave, placement, playlist and level fields (`speed` included), bad `kind`, pool without `min_level`, fixed with `min_level` (also `null`), `min_level` 0 and 9, negative and fractional `extra_rest_ticks`, bad wave file names (`Bad`, `1a`, `a-b`, empty, `ok\n`, `_x`), a non-object wave file, placement and level, a non-list `placements` and `fixed`, 7 and 9 levels, a negative and a boolean `random_count`, a non-string `fixed` entry, an unknown `fixed` entry, an unknown `variant`, `invert` on a meteorite, `specialty` on a meteorite, a bad `type` (types listed in enum order), `as_level` 0, 9, `true`, 2.0. A pool wave in `fixed` and as Wave 0 is accepted, as the contract says.
   - Order: two bad waves (`zz`, `aa`) report `aa` first. A wave with an unknown field and a bad `length_px` reports the unknown field first (the contract's order).
   - Same inputs twice: identical output for the whole edge run (`cmp` identical), equal books. Inputs not mutated (JSON dump compared). `DrifterTuning` not mutated. No log line from `build_wave_book` (root logger at DEBUG; the only line was the app's own tuning load).
4. **Assumptions:** The contract fixes the order of fields inside a wave file only roughly. The code checks `placements` is a list before `min_level`; I did not treat that as a bug. The `g` format shows 119.999999 as "120 px" in the seam message, as the contract's `g` rule says.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. No open bug. Non-blocking notes the Architect may read (already in the review): a wave file named `playlist` is not refused (review F5), and `extra_rest_ticks` has no upper limit, so a 400-digit integer is accepted and would hold a rest forever. The contract sets no cap, so it is not a bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
