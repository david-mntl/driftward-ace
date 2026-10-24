Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Add the `seed` placement field, the default seed and the one-path-per-UFO check to the wave loader. Task `docs/contracts/DRA-104/tasks/DRA-104-02-gameplay-implementer.md`, from the Architect.

2. **Delivered:** `game/core/wave_files.py` (changed).

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/wave_files.py`: clean.
   - `game/tests/check.sh lint`: PASS lint, PASS format. `check.sh typecheck`: PASS, no issues in 78 files.
   - Acceptance command (the task's script, run from `game/` with `PYTHONPATH=.` as a file; same code, SDL dummy drivers set). Output, seven lines as the task expects:
     ```
     ('meteorite', None) ('ufo', 5) True
     waves/wave_0.json: placements[1]: seed 5 is already used by placements[0]
     waves/wave_0.json: placements[0].seed must be an integer from 0 to 4294967295
     waves/wave_0.json: placements[0].seed must be an integer from 0 to 4294967295
     waves/wave_0.json: placements[0]: ufo placement y 100 is outside its band 188 to 440
     waves/wave_0.json: placements[0].type 'comet' is not a drifter type (meteorite, satellite, chain_lightning, fireball, coin, floating_island, planet, ufo)
     waves/wave_0.json: placements[2]: meteorite has no seed
     ```
   - Determinism: ran it twice, output identical (diff empty).
   - Grep of `game/core/` for the forbidden names: the only hits are `waves.py`/`wave_id` matching `.wav` and the ruff bans in `core/ruff.toml`. No real hit.
   - `check.sh core`: fails at collection, `tests/core/test_collision.py:1753 KeyError: 'hitbox'` (reads a tuning file). `check.sh ui`: one failure, `tests/ui/test_drifter_registry.py::test_drifter_lists_match_everywhere`. Both are of the kind the task allows (UFO tuning file, view and QA tasks not done). I did not look into them further.

4. **Assumptions:** The one-path check runs on the placements in file order, before the sort by `at_px`, as the contract says ("index in the file"). A seed of None is skipped in the check, since only seeded drifters carry one by then.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-104/tasks/DRA-104-02-gameplay-implementer.md`. I left `game/core/waves.py`, `game/core/run.py`, the drifters, tests and wave files alone.

7. **Status:** done.

## Decisions
- `seed` is a placement field read with `_is_seed`: an int (not a bool) from 0 to `MAX_SEED`. The message is built from `MAX_SEED`, so it says 4294967295 with no number typed in.
- Default seed: `placement_seed(wave_id, index)` when the file gives none and `drifter_class(type).seeded` is True. Index is the position in the file's list. Source: waves.md, Rules, Built drifter.
- A seed on an unseeded drifter is passed on, so the load-time spawn refuses it (`meteorite has no seed`). No separate check in the loader.
- `_build_placement` now takes the wave id instead of the file name, so it can build the default seed. It rebuilds the file name the same way `_build_wave` does.
- `_check_one_path_per_seed` runs after all placements are built and spawned, so earlier errors (a band refusal, a bad field) come first. It names the later placement and the first user of the seed. Seeds are never compared across waves.
