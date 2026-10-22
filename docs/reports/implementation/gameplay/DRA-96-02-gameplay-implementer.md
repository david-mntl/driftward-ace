Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-96/tasks/DRA-96-02-gameplay-implementer.md`: add the planet drifter, `DrifterType.PLANET`, the `gravity_well` and `start_size` base hooks, and the spawner's use of `start_size` (from the Architect).
2. **Delivered:**
   - `game/core/drifters/base.py` (changed): `GravityWell` import, `DrifterType.PLANET`, `Drifter.gravity_well` (None), classmethod `Drifter.start_size` (the footprint).
   - `game/core/drifters/spawner.py` (changed): step 7, `start_position` gets the sizes from `cls.start_size`.
   - `game/core/drifters/planet.py` (new): `FIELD_DRAW_MARGIN`, `PlanetVariantExtra`, `PlanetTypeExtra`, `FieldRing`, `planet_hitbox`, `Planet`.
   - `game/core/drifters/__init__.py` (changed): the `planet` import.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `python -m py_compile` on the four files: clean.
   - `ruff check game`: all passed. `ruff format --check game`: 78 files formatted. `game/tests/check.sh lint`: pass. `typecheck`: pass (mypy strict, 74 files).
   - `check.sh core`: 2827 passed, 4 failed. `check.sh ui`: 45 passed, 1 failed. All five are the failures the drifters contract's DRA-96 Impact table expects until later tasks exist: `test_collision.py::test_ship_meets_every_variant...[planet-None]` (no `planet.json`, DRA-96-06), the three `test_wave_files.py` unknown-type refusals (the type list gains `planet`, DRA-96-07) and `test_drifter_registry.py::test_drifter_lists_match_everywhere` (no `planet.json`, no `planet_view.py`, DRA-96-04). Every other test passes unchanged, so every older drifter starts where it did.
   - Acceptance command, from `game/`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<the command in the task file, verbatim>"`. Output, eight lines as the task expects:
     ```
     warning -151.0 0.0 (320.0, 12.0) None ()
     active -151.0 False (Circle(cx=320.0, cy=-151.0, r=32.0),)
     GravityWell(x=320.0, y=-151.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2)
     [(150.0, 0.5), (91.0, 0.25)]
     -149.9 True 302.0 hit
     planet has no speed
     planet has no invert
     planet placement needs x
     ```
   - Determinism: ran the same command twice, outputs identical.
   - Grep of `game/core/` for the banned names: only false hits (`asyncio.sleep` in a `ruff.toml` message, `waves` matching `.wav` in `run.py`, `waves.py`, `wave_files.py`). None in the files I changed.
4. **Assumptions:** None. The `PERCENT` constant (100.0) in `planet.py` turns `field_ring_fade` percent into a 0..1 share; it is a unit conversion, not a game value.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-96/tasks/DRA-96-02-gameplay-implementer.md`. `load_tuning` in `game/app/` raises at startup until `planet.json` and its loader exist (Impact table; Integration Engineer). Left alone: `game/core/ship.py` (DRA-96-01), `game/core/run.py` (DRA-96-03), the view, `game/app/`, `game/tuning/drifters/planet.json`, tests, the other drifters, `core/collision.py`, `core/levels.py`, `core/drifters/tuning.py`.
7. **Status:** done.

## Decisions
- `start_size` is a classmethod hook on the base returning `(width, height)`; the planet overrides it with `2 x (pull_radius + FIELD_DRAW_MARGIN)` (302 at the file's values). Without a `PlanetVariantExtra` it falls back to `(width, height)` and `born` refuses that tuning right after, as the contract says. Source: drifters.md, Rules, The base (Start size).
- `Planet.born` checks specialty, then invert, then the two extras, in that order. It does not call `Drifter.born`, because it needs its own extras check. The spawner's parked rule raises `planet has no speed` before `born` runs. Source: drifters.md, Rules, Planet (Born).
- `Planet.update`: `tick_warning` in WARNING; in ACTIVE `y += ctx.scroll_step_px` and `ticks_in_phase + 1`; GONE unchanged. The ship in `ctx` is never read. The contract fixes the order, so no Euler choice applies.
- `inner_rings` follows the contract formula with Python's `%`: `k = (ticks_in_phase - i x gap) % trip`, linear radius and linear opacity. Result matches the contract's timeline table at t = 0 (150.0 / 0.5 and 91.0 / 0.25).
- `drawn_parts` and `start_size` share one private helper, `_field_box_side`, so the 302 px box is worked out in one place.
- Every number (size, pull, rings, warning length) comes from `Birth` through the tuning records. The only constants are `FIELD_DRAW_MARGIN` (contract: not a game value) and `PERCENT`.
