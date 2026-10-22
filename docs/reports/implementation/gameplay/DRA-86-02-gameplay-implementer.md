Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the floating island drifter, `DrifterType.FLOATING_ISLAND` and `TouchEffect.BLOCK`, from `docs/contracts/DRA-86/tasks/DRA-86-02-gameplay-implementer.md` (Architect).
2. **Delivered:**
   - `game/core/drifters/base.py` (changed): `DrifterType.FLOATING_ISLAND`, `TouchEffect.BLOCK`.
   - `game/core/drifters/floating_island.py` (new): `IslandShape`, `INVERTIBLE_SHAPES`, `IslandVariantExtra`, `IslandTypeExtra`, `island_hitbox`, `FloatingIsland`.
   - `game/core/drifters/__init__.py` (changed): one import line for `floating_island`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: pygame-ce 2.5.8.
   - `python -m py_compile` on the three files: clean.
   - `ruff check .` and `ruff format --check .` in `game/`: clean. `game/tests/check.sh lint`: pass.
   - Acceptance smoke (the task's command, saved as a scratch script outside the repo and run from `game/` with `PYTHONPATH=.`, `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`). Output, seven lines as the task expects:
     ```
     active -60.0 0.0 block ()
     -58.9 320.0
     (Box(cx=0.0, cy=-40.0, w=320.0, h=40.0), Box(cx=-140.0, cy=0.0, w=40.0, h=120.0))
     (Polygon(points=((-160.0, 60.0), (160.0, -60.0), (-160.0, -60.0))),)
     floating_island variant 'box' has no invert
     floating_island has no speed
     floating_island placement needs x
     ```
   - Determinism: ran twice, output byte-identical.
   - Grep of `game/core/` for the banned terms: no real hits. The matches are `.waves` (the `\.wav` pattern) in `core/waves.py` and `core/run.py`, and the ban messages in `core/ruff.toml`.
   - `check.sh typecheck`: 6 errors, all in `tests/core/test_collision.py:589,596` (Polygon in the shape unions), expected by the Impact table. `check.sh core`: 5 failures, all expected: `test_collision.py` (the shape-kind table, the ship-against-every-variant case for `floating_island`) and `test_wave_files.py`'s three placement-type-list messages. `check.sh ui`: 1 failure, `test_drifter_registry.py` (no `floating_island.json` and no view yet). 1572 core and 45 ui tests pass unchanged.
4. **Assumptions:** None.
5. **Documentation differences:** None. One note, not a difference: the `spawn_drifter` docstring in `spawner.py` still says "or ACTIVE for the coin". I left it alone, as the task doesn't name `spawner.py`.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-86/tasks/DRA-86-02-gameplay-implementer.md`. Left alone: `spawner.py` (its parked rule already covers the island), `game/tuning/` (the island's file is content), the views and tests.
7. **Status:** done.

## Decisions
- `born` mirrors the coin's: specialty refusal, `IslandVariantExtra` and `IslandTypeExtra` checks, then the invert check on `IslandShape` against `INVERTIBLE_SHAPES`, in the contract's order and with its exact messages. The hitbox is rebuilt in `born` with `island_hitbox(..., birth.invert)`, so `invert` is applied in one place.
- `island_hitbox` is a `match` on the shape with the contract's formulas, every number a float. It has no default branch: the four members are covered, so a new shape fails type checking until handled.
- `update` follows the coin: `y += ctx.scroll_step_px` while ACTIVE, plus `ticks_in_phase + 1`. No speed, no sideways move.
- `drawn_parts`, `collect_points`, `collect_popup` and `graze_zone` are the base's, as the contract says. `graze_zone` is `()` because the effect is BLOCK, not HIT.
- Every number comes from `Birth` (the tuning file through `app.tuning`). No constant of mine in code except the `INVERTIBLE_SHAPES` set the contract gives.
- No logging, as the contract's Logging rule says for `core.drifters.*`.
