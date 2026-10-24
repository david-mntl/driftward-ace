Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-104-02-gameplay-implementer (the `seed` placement field, default seeds and the one-path-per-UFO check in the wave loader), started by /implement. Review status was `reviewed` (two notes, no change asked).
2. **Delivered:** docs/reports/qa/DRA-104-02-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck pass. `core` and `ui` fail, and only in the three places the task and the DRA-104 Impact tables name (see Harness). No failure comes from `game/core/wave_files.py`.
   - Acceptance check: I ran the task's command exactly (from `game/`, `PYTHONPATH=.`, SDL dummy). The seven lines match the task, line for line: `('meteorite', None) ('ufo', 5) True`, then the duplicate-seed, `-1`, `true`, band, `comet` and meteorite-seed messages. Run twice: identical output.
   - Seed values: 0 and 4294967295 load (UFO gets that seed). 4294967296, 5.0, "5", true, false, null and 2^70 are each refused with `waves/wave_0.json: placements[0].seed must be an integer from 0 to 4294967295`.
   - Default seed: with no `seed` and `at_px` 500, 200, 900 in the file, the seeds are `placement_seed('wave_0', 0, 1, 2)` by file index (293031380, 2630326367, 2057624744), not by sorted position. A second load of a copy gives the same. `placement_seed` is the same under `PYTHONHASHSEED` 0, 1 and 999.
   - One path per UFO: the same seed in two different waves loads. In one wave the later placement by file index is refused and the first user is named: `placements[2]: seed 1 is already used by placements[0]` in `[1, 2, 1, 1]`; with `[1, 2, 2, 1]` it is `placements[2]: seed 2 ... placements[1]`. A given seed equal to another UFO's default is refused (both orders: `placements[1]: seed 293031380 is already used by placements[0]` and `... 2630326367 ... placements[0]`). Two meteorites with no seed never clash.
   - Order of errors: duplicate seed plus a UFO outside its band: the band error comes first (`placements[2]: ufo placement y 100 is outside its band 188 to 440`, and `placements[1]` when that one is both a duplicate and out of band). A seed on a meteorite: `placements[0]: meteorite has no seed`; a non-integer seed on a meteorite is the seed-field message. A meteorite with no seed keeps `seed` None. A UFO at 0 px and at 119.9 px is refused by the seam rule; `speed` on a UFO is `unknown field 'speed'`; a UFO with no `y` is `ufo placement needs y`.
   - Existing waves: the seven committed wave files load through `app.waves.load_wave_book` (with the UFO's tuning left out, see Assumptions) and no placement has a seed.
   - Edge cases that behave correctly are not listed further. No bug found.
4. **Assumptions:** `app.tuning.load_tuning()` raises `tuning/drifters/ufo.json: band_bottom is not a known field`, because the app's tuning loader has no UFO branch yet. The app contract gives that file's loader to the Integration Engineer during DRA-104 integration (app.md, Roles), so I did not file it. To load the committed waves I built the tuning with the UFO left out. The 02 task says `core` and `ui` may fail until the view, the tuning file and the QA tasks exist, so I took the three harness failures below as expected, not as bugs.
5. **Documentation differences:** None.
6. **Next:** No bug is open for DRA-104-02. The verdict is `blocked` only because `check.sh` does not end `QA: pass`, and every failure comes from a later queued task: DRA-104-03 (view), DRA-104-04 (the collision test's UFO case) and DRA-104-06 (the unknown-type rows). The /implement skill can continue and re-check this task's harness after those three. Open from DRA-104-01: its B1 (`docs/reports/qa/DRA-104-01-gameplay-implementer.md`), Gameplay Implementer.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL · ui FAIL
- core: `tests/core/test_collision.py` fails at collection, `KeyError: 'hitbox'`: its ship-against-every-variant loader reads `game/tuning/drifters/ufo.json`, which has `disc_width`, `disc_height` and `dome_radius` and no `hitbox`. Task DRA-104-04. With that file ignored: 744 passed, 3 failed: `test_a_bad_set_raises_value_error_naming_the_file_and_the_problem` for `placement type 'ufo'`, `'Meteorite'` and `''`. The unknown-type list now ends `planet, ufo`. Task DRA-104-06.
- ui: `tests/ui/test_drifter_registry.py::test_drifter_lists_match_everywhere` fails: no registered view for `ufo`. Task DRA-104-03. 45 other ui tests pass.
QA: fail (core ui)

## Round 2 2026-10-22

1. **Task:** Re-test of DRA-104-02-gameplay-implementer after DRA-104-03, 04 and 06 landed, started by /implement. The round 1 verdict was `blocked` only because `check.sh` failed on files those tasks fix.
2. **Delivered:** this round in docs/reports/qa/DRA-104-02-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: every step passes and the last line is `QA: pass` (core 3132 passed, ui 46 passed).
   - Acceptance check: the task's command run again from `game/` (`PYTHONPATH=.`, SDL dummy). The seven lines match the task: `('meteorite', None) ('ufo', 5) True`, the duplicate-seed line, `seed must be an integer from 0 to 4294967295` twice, the band line, the `comet` line and `placements[2]: meteorite has no seed`. Two runs: identical output.
   - The three round 1 failures are gone: the collision test's UFO case (DRA-104-04), the unknown-type rows (DRA-104-06) and the registry test (DRA-104-03). No code in `game/core/wave_files.py` or `game/core/drifters/spawner.py` was changed for this round, and the round 1 edge cases (seed range and type, default seed by file index, one path per UFO, error order) were not re-opened.
   - DRA-104-01's B1 is fixed and re-tested in its own report. It is not open here.
4. **Assumptions:** The `app.tuning` UFO loader gap noted in round 1 stays with the Integration Engineer (app.md, Roles). Not a bug for this task.
5. **Documentation differences:** None.
6. **Next:** No bug is open. Integration Engineer.
7. **Status:** done.

## Bugs
None open. Round 1 had none.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
