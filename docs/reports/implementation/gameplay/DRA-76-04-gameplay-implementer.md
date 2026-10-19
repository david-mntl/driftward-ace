Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** build `game/core/wave_files.py` (`build_wave_book`), the load-time check that turns decoded wave and playlist JSON into a `WaveBook` or raises `ValueError` (task `docs/contracts/DRA-76/tasks/DRA-76-04-gameplay-implementer.md`, from the Architect).
2. **Delivered:** `game/core/wave_files.py` (new). Nothing else changed.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile game/core/wave_files.py`: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 68 files already formatted. `mypy --strict` on the file: no issues.
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS; last line `QA: pass`.
   - Smoke (acceptance check), from `game/`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<the command in the task's Acceptance check>"`. Output:
     ```
     ['p', 'w0'] w0 [0.0, 150.0] 0 30 ('p',)
     waves/w0.json: placements[0]: a hazard (meteorite) at 100 px is inside the first 120 px
     accepted
     waves/playlist.json: wave_zero names 'nope', which is not a wave
     waves/playlist.json: levels[0] (level 1) has random_count 1 but no pool wave with min_level <= 1
     ```
     Run twice: identical output. I ran it as the same code fed on stdin from `game/`.
   - Extra refusals tried and matching the contract's example wording: `speed` on a placement, unknown variant, unknown drifter type (types listed in enum order), negative `at_px`, `length_px` as a bool, unknown wave field, `min_level` missing on a pool wave, `min_level` on a fixed wave, bad file name, a meteorite with no `x`, a hazard at exactly 120 px (accepted), 7 playlist levels, no pool wave at Level 8, an unknown fixed entry, a negative `random_count`.
   - Grep of `game/core/wave_files.py` for the banned names: one hit, `from core.waves import ...`, which matches the pattern `.wav` by accident (the module name `waves`). No real hit.
4. **Assumptions:**
   - A number must also be finite. Python's JSON decoder accepts `NaN` and `Infinity`; the contract says only "a number". I refuse them with the same "must be a number ..." message, as a wave of infinite length would never end.
   - Messages the contract gives no example for follow its pattern: `<file>: <path>.<field> must be <needs>`, e.g. `placements[0].x must be a number`, `kind must be "fixed" or "pool"`, `placements must be a list`, `waves/<id>.json: must be a JSON object`, `placements[i]: must be an object`, `levels[i].fixed[j] must be a string`.
   - Order inside a wave file: object, unknown fields, `length_px`, `kind`, `placements` is a list, `min_level`, `extra_rest_ticks`, then each placement. Inside a placement: object, unknown fields, `at_px`, `type`, `variant`, `invert`, `as_level`, `x`, `y`, `specialty`, then drifter type, spawn, seam. The contract fixes the order only roughly ("fields in the order below").
   - The playlist's whole shape is checked before the named-waves check. A wave file named `playlist` is not refused (the contract lists no such check; the app is expected to read that file as the playlist).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-76/tasks/DRA-76-04-gameplay-implementer.md`. I left `game/core/waves.py` and the other uncommitted files alone.
7. **Status:** done.

## Decisions
- Errors are built by a small frozen `_Where(file, path)` that returns the `ValueError` (`error` for a whole object, `error_field` for one field). Callers `raise` it, with `from` where an exception is being converted (unknown drifter type, spawner errors). One place owns the message shape.
- Field checks are small `TypeGuard` predicates passed to one generic `_checked` / `_checked_optional`, so each field is one line and every message says what the field must be. `bool` is excluded from numbers and integers in the predicates.
- Every placement is spawned once with `spawn_drifter(placement, FIRST_LEVEL, tuning)`; `ValueError` from it is re-raised naming the placement. The hazard test reads `effect_on_touch() is TouchEffect.HIT`, so a new hazard type needs no change here. Source: waves.md, Rationale, "Every placement is spawned once at load".
- Placements sorted with a stable `sort` on `at_px` (ties keep file order). Waves are inserted in id order. Source: waves.md, Built.
- `SEAM_CLEAR_PX` 120 (locked, 09-waves.md seam_clear), `NAME_PATTERN`, `WAVES_FOLDER`, `PLAYLIST_NAME`: the contract's Interface. Level count and first level from `core.levels`; no number copied.
- Not checked, as the contract says: seam at a wave's end, placements past the wave's length, empty playlist levels, pool waves named in `fixed`, Wave 0's hazard types.

## Review fix 2026-10-19: docs/reports/review/DRA-76-04-gameplay-implementer.md

Fixed: DRA-76-04-F1
Not fixable: DRA-76-04-F2 (note, the review asks for no change)
Not fixable: DRA-76-04-F3 (note, the review asks for no change; the import list is the Architect's)
Not fixable: DRA-76-04-F4 (note, the review asks for no change)
Not fixable: DRA-76-04-F5 (note, the review asks for no change; a `playlist` wave-name check needs a contract change)

Round 1 covers every finding whose change is not "none": only F1.

1. **Task:** fix review finding F1 on `game/core/wave_files.py`: an int too large for a float crashed `_is_number` with `OverflowError` (review round 1, from the `/implement` skill).
2. **Delivered:** `game/core/wave_files.py:114-123` (`_is_number`).
3. **Checks:**
   - IS_CE passes. py_compile clean. `ruff check game` and `ruff format --check game` pass (68 files formatted). `mypy --strict` on the file: no issues. `game/tests/check.sh`: `QA: pass`.
   - Smoke from `game/` (acceptance check plus three huge-int cases, `10**400`), run twice, identical output (same md5). Run as `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python < <script>`. The first five lines are unchanged from the original delivery. The new lines:
     ```
     waves/w0.json: length_px must be a number > 0
     waves/w0.json: placements[0].at_px must be a number >= 0
     waves/w0.json: placements[0].x must be a number
     ```
   - Grep: one hit, `from core.waves import ...`, matches `.wav` by accident. No real hit.
4. **Assumptions:** None new. The huge int gets the same "must be a number ..." message as other non-numbers.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-76-04-gameplay-implementer.md`.
7. **Status:** done.

**Decisions**
- `_is_number` returns False when `math.isfinite` raises `OverflowError`. The guard sits in the one predicate every number check goes through, so `float(at_px)` and `float(length_px)` later cannot see a huge int.

**Answers**
- DRA-76-04-F1. Fixed: game/core/wave_files.py:114-123, `_is_number` catches `OverflowError` and returns False, so the file is refused with "must be a number ...".
- DRA-76-04-F2. Not fixable: note, no change asked.
- DRA-76-04-F3. Not fixable: note, no change asked.
- DRA-76-04-F4. Not fixable: note, no change asked.
- DRA-76-04-F5. Not fixable: note, no change asked.
