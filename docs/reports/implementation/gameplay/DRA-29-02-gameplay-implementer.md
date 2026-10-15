Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-29-02 (Architect): the level table, the object base, tuning records, registry, spawner and meteorite, from `docs/contracts/systems/objects.md`.
2. **Delivered:**
   - `game/core/levels.py`
   - `game/core/objects/__init__.py`
   - `game/core/objects/base.py`
   - `game/core/objects/tuning.py`
   - `game/core/objects/registry.py`
   - `game/core/objects/spawner.py`
   - `game/core/objects/meteorite.py`
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `py_compile` on all seven files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `typecheck` (mypy strict): PASS, 32 files. `core`: 35 passed (every existing test).
   - Smoke run, the task's acceptance command, from `game/` (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<acceptance script>"`). Output, seven lines as the task expects:
     ```
     ['meteorite']
     medium -14.0 4.935 warning ()
     warning -14.0
     active -14.0 1
     -9.065 320.0
     7.008
     unknown variant 'huge' for object type 'meteorite'
     ```
   - Determinism: the smoke run twice, output identical.
   - Registry: `register_object(GameObject)` raises `TypeError`; registering `Meteorite` a second time raises `ValueError("object type 'meteorite' is already registered")`. `check_level(9)` raises `level 9 is outside 1 to 8`.
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: only hits are the ban list text in `core/ruff.toml`. No code hit.
4. **Assumptions:**
   - `level_at` returns `max(1, count of starts <= meters)`, so a negative distance gives Level 1 rather than 0. The contract doesn't cover negative meters.
   - The two `TypeError` messages of `register_object` (abstract class, no `object_type`) are mine; the contract gives only the `ValueError` ones.
   - `spawn_object` checks in the contract's step order: class, tuning, variant, level. So an unknown variant is reported before a bad level.
   - `placement.variant or default_variant`: an empty string variant is treated as unset.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-29/tasks/DRA-29-02-gameplay-implementer.md`. Left alone: `core/ship.py` and `core/collision.py` (task DRA-29-01), `core/run.py` (task DRA-29-03), `game/tuning/`, tests.
7. **Status:** done.

## Decisions
- Registry state: `registry.py` holds one module-level dict `_CLASSES`. The contract requires a registry filled by a decorator at import, so this is the one module state; it is private and only `register_object` writes it.
- `register_object` and `tick_warning` use PEP 695 type parameters (`def f[G: GameObject](...)`) instead of the contract's `TypeVar`. Ruff rule UP047 (target py312) fails the `TypeVar` form. The signature is equivalent.
- `core/objects/__init__.py` imports `from core.objects import meteorite as meteorite`. The alias form is an explicit re-export, so ruff F401 passes without `# noqa`.
- `GameObject` and `Specialty` are `kw_only=True` as the task says, which lets `uid: int = 0` sit before the required fields. `from __future__ import annotations` handles the `GameObject` and `Specialty` cross-reference. No zero-argument `super()`.
- `BASE_LEVEL: Final[int] = 1` in `spawner.py` names the "Level 1 values" a playtest switch falls back to. Not a GDD number beyond "Level 1".
- Switches beat `as_level`: `use_level` is still checked with `check_level`, then each switch picks level 1 for its own multiplier. Entry warnings are copied from tuning unscaled.
- `Meteorite.update` returns `self` in GONE. `may_hit_ship` is documented as the LD-06 stand-in.
- Every number is from `core/levels.py` (08-difficulty.md), `GRAZE_MARGIN` (06-scoring.md, locked) or the tuning records. Speed uses `TOP_SIDE_SPEED` from `core/ship.py`. No log lines; each module with code has `log`. `__init__.py` has none, as the contract says "docstring and nothing else".

## Review fix 2026-10-15: docs/reports/review/DRA-29-02-gameplay-implementer.md

1. **Task:** Round 1 review fix for DRA-29-02 (Implementation Reviewer): answer findings 1 and 2. Notes 3, 4 and 5 ask for no change.
2. **Delivered:**
   - `game/core/objects/spawner.py` (variant fallback only for `None`)
   - `game/core/objects/base.py` (member doc on `ObjectType.METEORITE`)
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes. `py_compile` on both files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `typecheck`: PASS. `core`: PASS.
   - Smoke run: the task's acceptance script from `game/` (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <script>`) prints the same seven lines as before. One added case, `variant=''`, prints `unknown variant '' for object type 'meteorite'`.
   - Determinism: run twice, identical output (same md5).
   - Grep of `game/core/` for the banned names: no hits.
4. **Assumptions:** Old Assumption 4 (empty variant treated as unset) is withdrawn. The contract answers it.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, on `docs/reports/review/DRA-29-02-gameplay-implementer.md`.
7. **Status:** done.

## Decisions
- Variant fallback uses the `is None` form, matching the `as_level` and `y` lines in the same function. Source: `docs/contracts/systems/objects.md`, Rules, Spawner, step 2.
- The member doc on `METEORITE` names its source, `objects/01-meteorite.md`, as the contract's Interface comment does.

## Answers
1. Fixed: `game/core/objects/spawner.py:59-61`, `variant=""` now raises `unknown variant '' for object type 'meteorite'`; Assumption 4 withdrawn above.
2. Fixed: `game/core/objects/base.py:31`, added a docstring under `METEORITE` naming `objects/01-meteorite.md`.
