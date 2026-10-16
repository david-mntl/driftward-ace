Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** build the satellite drifter (`DrifterType.SATELLITE`, `satellite.py`, its import), task `docs/contracts/DRA-39/tasks/DRA-39-03-gameplay-implementer.md`, from the Architect.
2. **Delivered:**
   - `game/core/drifters/base.py`: the `SATELLITE` member of `DrifterType`.
   - `game/core/drifters/satellite.py` (new): `SatelliteVariantExtra` and `Satellite` (`born`, `start_position`, `update`, `effect_on_touch`, `warning_tilt_degrees`), registered with `@register_drifter`.
   - `game/core/drifters/__init__.py`: one import line for `satellite`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on the three files: clean.
   - `ruff check game`: all passed. `ruff format --check game`: 48 files formatted. `game/tests/check.sh lint`: PASS lint, PASS format.
   - `check.sh typecheck`: 18 errors, `tests/core/test_drifters.py` (3) and `tests/core/test_run_drifters.py` (15), all `hit_ship`. `check.sh core`: 16 failed, 49 passed, in the same two files (4 and 12). This is exactly the DRA-39-01 list; no new failure.
   - Smoke run: the acceptance command, from `game/`, with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<the acceptance script, unchanged>"` (I ran the same script from a file with `PYTHONPATH=.`). Output:
     ```
     ['meteorite', 'satellite']
     flat -18.0 300.0 (18.0, 300.0) True ()
     active -15.5325 300.0 2
     658.0 (622.0, 200.0) 20.0 -2.3187 0.8439
     satellite placement needs y
     ```
     All five lines match the task.
   - Determinism: two runs, output identical (diff empty).
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: the only hits are two lines in `game/core/ruff.toml` (the ban messages for `threading` and `time.sleep`). No code hit.
4. **Assumptions:** `SatelliteVariantExtra.angle_degrees` is stored on the drifter as `float(...)`, so an int angle in tuning (the acceptance script passes `20`) still gives a float tilt (`20.0`, as the task prints).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-39/tasks/DRA-39-03-gameplay-implementer.md`. Left alone: `satellite_view.py` (DRA-39-04), `game/tuning/drifters/satellite.json` and its loader in `game/app/` (Integration Engineer; `load_tuning` raises until then, as the contract says), and every test (DRA-39-05 to 07). The `core` and `typecheck` failures stay until DRA-39-06 and DRA-39-07.
7. **Status:** done.

## Decisions
- `born` does its own two checks instead of calling the base `born`: the base would refuse `invert`, which the satellite accepts. The order follows the contract: specialty, then the extra, then `replace(born_drifter(...))`.
- A variant extra that is missing or not a `SatelliteVariantExtra` raises `ValueError("satellite variant '<name>' has no angle")`, as the contract says.
- Velocity: `speed * cos(angle)` (negated with `invert`) and `speed * sin(angle)`. `speed` already carries the hazard speed multiplier, so the angle never scales (spec rule 6). Source: contract, Rules, Satellite, Born.
- `start_position` checks y first, then x. A given x is kept (07-drifters.md, rule 14); a missing x is `-width / 2` or `SCREEN_W + width / 2`. `SCREEN_W` comes from `core.world`, no number in code.
- `warning_tilt_degrees` returns `angle_degrees` with `invert` and `-angle_degrees` without. Flat gives -0.0, which equals 0 and hashes like 0.0, so the warning cache key is unaffected.
- `update` mirrors the meteorite: WARNING through `tick_warning`, ACTIVE adds the velocity and one tick, GONE unchanged. The ship in `ctx` is never read. Update order is plain position += velocity, no walls: the satellite flies through them (Rules, Leaving).
- No new number in code: speed, angle, size and hitbox come from tuning; the cooldown from the base.
