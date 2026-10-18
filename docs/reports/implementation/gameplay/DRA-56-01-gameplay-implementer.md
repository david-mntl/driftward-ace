Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the fireball in core and the base `drawn_parts` hook it needs: `docs/contracts/DRA-56/tasks/DRA-56-01-gameplay-implementer.md` (Architect, Linear DRA-57).

2. **Delivered:**
   - `game/core/drifters/base.py` (changed): `DrifterType.FIREBALL`, `drawn_parts()`, `is_partly_on_screen()` and `is_off_screen()` judged on it, the `Box` import, two private box tests `_box_on_screen` and `_box_past_edge`.
   - `game/core/drifters/fireball.py` (new): `DRAW_MARGIN`, `FireballTypeExtra`, `fireball_hitbox`, `Fireball`.
   - `game/core/drifters/__init__.py` (changed): one import line, `fireball`.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `py_compile` on the three files: clean.
   - `ruff check game` and `ruff format --check game`: no findings. `game/tests/check.sh lint` and `typecheck` (mypy strict, 52 files): pass.
   - Acceptance smoke, from `game/`, with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`: all twelve lines match the task's expected output. Run twice: byte-identical output. I ran the command body as a script with `PYTHONPATH=.` (same imports, same lines).
   - `check.sh core -k "not collision"`: 104 passed. `check.sh core`: 1312 passed, 1 failed, only `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[fireball-None]`. `check.sh ui`: 1 failed, only `test_drifter_registry.py::test_drifter_lists_match_everywhere`. Both are the failures the task expects until DRA-56-02, DRA-56-03 and `game/tuning/drifters/fireball.json` exist.
   - Grep of `game/core/` for the banned names: the only hits are the ban messages in `game/core/ruff.toml` (not code). No hit in any `.py`.

   Command and output (command body as in the task's Acceptance check):
   ```
   ['chain_lightning', 'fireball', 'meteorite', 'satellite']
   small 0.00 -10.50 12.00 12.00 35.0 1.7738 2.5333
   big 640.00 -16.00 628.00 12.00 -35.0 -1.7738 2.5333
   small 125.00 -10.50 125.00 12.00 35.0 1.7738 2.5333
   small -10.50 120.00 12.00 120.00 35.0 1.7738 2.5333
   small 650.50 200.00 628.00 200.00 -35.0 -1.7738 2.5333
   0.00,0.00,10.50 -9.03,-12.90,5.25 | 0.00,0.00,16.00 13.77,-19.66,8.00
   0.00,-10.50,24.00 -9.03,-23.40,13.50 | 640.00,-16.00,35.00 653.77,-35.66,19.00
   21.00 31.50 0.00,5.25,10.50 0.00,-10.50,5.25 warning
   [(60, 'active', True, '125.00', '-10.50', False), (258, 'active', True, '476.22', '491.10', False), (261, 'active', True, '481.54', '498.70', False), (262, 'active', True, '483.32', '501.23', True)]
   4.39 2.52 3.60 35.0
   fireball has no specialty
   ```

4. **Assumptions:** None beyond the contract. `drawn_parts()` on the fireball skips any non-circle shape in its hitbox (needed for mypy's narrowing); the hitbox is always two circles, so nothing is skipped.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-56/tasks/DRA-56-01-gameplay-implementer.md`. Left alone: the fireball view (DRA-56-02), `game/tuning/drifters/fireball.json` and its loader, the debug spawn rows, every test file, `core/run.py`, the other drifters.

7. **Status:** done.

## Decisions
- Update order: the fireball adds the final per-tick velocity to its position in ACTIVE, as the satellite does. No walls, no collision step here: it flies through walls and drifters (contract, Update; GDD 07-drifters.md, rule 15).
- Screen tests: `is_partly_on_screen` is `any` over `drawn_parts()`, `is_off_screen` is `all`, each box using the contract's four comparisons. With the base's one footprint box this is the DRA-39 behavior, so the meteorite, satellite and chain lightning are unchanged (their tests still pass).
- `fireball_hitbox` is the one place the tail's place is worked out. `born` recomputes the hitbox from it with `invert`, because the tuning file holds the un-inverted hitbox.
- `start_position` never raises. A set coordinate is kept; the defaults follow the contract's start table.
- Numbers: angle, tail ratio, head widths, speed ratio and warning length come through `Birth` (tuning). `DRAW_MARGIN` 1.5 is the contract's constant, not a game value (Rationale, DRA-56). No other number in code.
- Warning copy and tilt follow the contract formulas. The satellite's tilt sign is the reverse of the fireball's by design (copy laid straight down vs. laid flat).
