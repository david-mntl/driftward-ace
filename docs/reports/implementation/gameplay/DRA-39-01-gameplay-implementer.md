Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-39/tasks/DRA-39-01-gameplay-implementer.md` (Architect): unknown shapes raise, the shared re-hit cooldown, entering and leaving, start position, new placement fields, and the run's steps 3, 7, 8 and 9. The satellite is not built (task DRA-39-03).
2. **Delivered:**
   - `game/core/collision.py`: `place_hitbox`, `grow_hitbox`, `hitboxes_overlap` raise `TypeError("unknown shape kind '<class name>'")`.
   - `game/core/drifters/base.py`: `DEFAULT_REHIT_COOLDOWN_TICKS`, `DEFAULT_REHIT_DIM`, `VariantExtra`, the four new `Birth` fields, the fields `has_entered`, `rehit_cooldown_ticks`, `rehit_dim`, `rehit_ticks_left`, the methods `is_partly_on_screen`, `mark_entered`, `warning_tilt_degrees`, `may_hit_ship`, `brightness`, `born` with the specialty and invert checks, abstract `start_position`, and `born_drifter`. `is_off_screen` needs `has_entered`. Removed `hit_ship` and `default_y`. `DrifterType.SATELLITE` left out on purpose.
   - `game/core/drifters/tuning.py`: `VariantTuning.extra`, `HazardRules`, `DrifterTuning.hazards`.
   - `game/core/drifters/spawner.py`: `Placement.x` optional, `invert`, `speed`; steps 4, 7 and 8.
   - `game/core/drifters/meteorite.py`: `start_position`; removed `default_y` and its own `may_hit_ship`.
   - `game/core/run.py`: `mark_entered()` after each update (step 3), a hit sets `rehit_ticks_left` (step 7.3), new `_cool_down` (step 8), drop (step 9).
3. **Checks:**
   - `python3 -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python3 -m py_compile` on all six files: clean.
   - `game/tests/check.sh lint`: pass (ruff check and ruff format --check).
   - `check.sh typecheck`: 18 errors, all in `tests/core/test_drifters.py` and `tests/core/test_run_drifters.py` (`hit_ship`). `check.sh core`: 16 failed, 49 passed; every failure is in those two files (the tests named under Impact). No other test fails, so `test_run.py`, `test_collision.py` and the ui tests pass.
   - Smoke run, from `game/`, command: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -c "<the acceptance script, unchanged>"`. Output:
     ```
     -14.0 180 0.75 True 1.0 False
     1.42
     meteorite placement needs x
     meteorite has no invert
     unknown shape kind 'str'
     [60, 241] {60: (180, 0.75), 239: (1, 0.75), 240: (0, 1.0)}
     2 True False
     ```
     All seven lines match the acceptance check. `place_hitbox(('x',), 1, 1)` and `grow_hitbox((1,), 1)` also raise `unknown shape kind`.
   - Determinism: ran the smoke twice, byte-identical output.
   - Grep of `game/core/` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|random.random(|.mp3|.wav`: only hits are the ban list in `game/core/ruff.toml`, not code.
4. **Assumptions:** `hitboxes_overlap` validates every shape of both hitboxes up front, so a bad shape raises even when the other hitbox is empty. `Birth`'s new fields have no defaults, as the contract lists them. A placement `speed` of 0.0 is kept (`is None` check), which the acceptance check needs.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-39/tasks/DRA-39-01-gameplay-implementer.md`. Left alone on purpose: `game/core/drifters/satellite.py` and `DrifterType.SATELLITE` (DRA-39-03), `game/core/drifters/__init__.py`, `registry.py`, every test file (tasks DRA-39-06 and DRA-39-07 rebuild the two broken ones), `game/app/` and `game/tuning/`.
7. **Status:** done.

## Decisions
- Collision: `_require_known_shapes` runs at the top of `hitboxes_overlap`; `_move_shape` and `_grow_shape` end in `raise` instead of defaulting to a box. Source: drifters.md, Rules, Collision (Unknown shape kind).
- Cooldown counting (step 8): `_cool_down(outcome, stepped.drifters)` takes the drifters as they went into step 7. A drifter counts down only if it was above 0 going in. A cooldown that starts in step 7 needs `may_hit_ship()`, so it was 0 going in and is skipped; a cooling drifter is never in `touching`. This gives the "did not start this tick" rule without tracking uids. It runs on fall, protected and wait ticks too, and before the drop (step 9). Source: run.md, Rules, steps 7 to 9.
- The game-over tick runs in full, so cooldowns count on it. The frozen game-over branch is untouched.
- `mark_entered()` is called in `_update_drifters`, so the existing `drifter active` log still compares phases around the update. No log line added.
- `born` raises "has no specialty" before "has no invert". `born_drifter` builds from the shared fields; the `Self` return of `born` type-checks under mypy strict.
- Spawner order: `start_position` runs before `born`, so a missing x on a meteorite raises "needs x" first, as the acceptance check expects.
- Numbers: the 180 and 0.75 defaults live in `base.py` with their GDD source (05-lives-and-damage.md, rehit_cooldown and rehit_dim, both guess). Nothing else is hard-coded; speed comes from tuning or `Placement.speed`.
