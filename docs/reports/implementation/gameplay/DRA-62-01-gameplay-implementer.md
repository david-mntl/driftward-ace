Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the coin, the points popup and the parked-drifter rules in `game/core/`, from `docs/contracts/DRA-62/tasks/DRA-62-01-gameplay-implementer.md` (Architect).

2. **Delivered:**
   - `game/core/popup.py` (new): `PointsPopup` (with the `y` property) and `step_popups`.
   - `game/core/drifters/base.py`: `DrifterType.COIN`, `TouchEffect.COLLECT` docstring, `TickContext.scroll_step_px` (default 0.0), `Drifter.parked` (False), `collect_points` (0), `collect_popup` (None), the `core.popup` import.
   - `game/core/drifters/tuning.py`: docstrings only (`speed_ratio`, `entry_warning_ticks`).
   - `game/core/drifters/spawner.py`: the parked rule in a private `_birth_speed` helper (parked: speed 0.0, `ValueError("<type> has no speed")` if the placement sets a speed); `spawn_drifter` docstring.
   - `game/core/drifters/coin.py` (new): `CoinVariantExtra`, `CoinTypeExtra`, `coin_hitbox`, `Coin`.
   - `game/core/drifters/__init__.py`: the `coin` import.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile` on `popup.py` and every file in `core/drifters/`: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `check.sh typecheck`: PASS (mypy strict, 60 files).
   - Tests: `check.sh core`: 1342 passed, 1 failed. `check.sh ui`: 45 passed, 1 failed. The two failures are the two the contract's DRA-62 Impact table expects: `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[coin-None]` ("no tuning file for 'coin'") and `test_drifter_registry.py::test_drifter_lists_match_everywhere` (no `coin.json`, no view yet). Every other test passes unchanged.
   - Smoke run (the acceptance command, from `game/`, saved outside the repo and run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <script>`; the body is the task's command, verbatim). Output:
     ```
     active -10.0 0.0 collect ()
     -8.9 320.0 2
     50 PointsPopup(x=320.0, start_y=-10.0, points=50, lifetime_ticks=60, rise_per_tick=0.5, age_ticks=0)
     coin has no speed
     ```
     All four lines match the acceptance check.
   - Determinism: ran the smoke twice, output identical (`diff` empty).
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: only hits are the ban messages in `game/core/ruff.toml` (config, not code). None in code.

4. **Assumptions:**
   - `PointsPopup` is `kw_only=True` as the contract's Interface shows; the acceptance repr matches that field order.
   - The coin's `born` repeats the base's specialty and invert checks inline instead of calling `super().born`, because it must not build through the base `born` (which builds in WARNING) and slots dataclasses forbid zero-argument `super()`. Messages are the base's.
   - `core.popup` has a `log` and logs nothing, per the contract.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-62/tasks/DRA-62-01-gameplay-implementer.md`. Left alone: `game/core/run.py` and `scroll.py` (task DRA-62-02), the coin's view (DRA-62-03), the popup view (DRA-62-04), `game/tuning/drifters/coin.json`, `game/app/`, tests.

7. **Status:** done.

## Decisions
- The spawner's speed rule moved into `_birth_speed(cls, placement, type_tuning, speed_mult)`, so `spawn_drifter` stays short and the parked branch sits in one place. A parked class never reads `speed_ratio` or the hazard speed multiplier (contract, Spawner step 4). Order in the function: a placement speed on a parked drifter raises first, then 0.0.
- The coin is born ACTIVE through `replace(born_drifter(...), phase=Phase.ACTIVE, ticks_in_phase=0, ...)`, so no WARNING state exists and no entry warning can draw (contract, Coin, Born; Rationale).
- `Coin.update` moves by `ctx.scroll_step_px` only while ACTIVE and never reads the ship. Semi-implicit Euler does not apply: there is no velocity.
- `start_position`: x required (`coin placement needs x`), y default `-height / 2`, as the contract says.
- `drawn_parts` is two plain boxes with no `DRAW_MARGIN`: sizes are whole even px (contract, Rationale).
- Every number (points, sizes, popup ticks and rise) comes from `Birth` through `CoinVariantExtra` and `CoinTypeExtra`. No number is in code. The acceptance command's values are the contract's coin file values.
