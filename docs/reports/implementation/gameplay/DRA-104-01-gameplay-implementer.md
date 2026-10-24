Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Build the UFO and the placement seed in `game/core/drifters/` (task `docs/contracts/DRA-104/tasks/DRA-104-01-gameplay-implementer.md`, from the Architect, contract `docs/contracts/systems/drifters.md` v8).

2. **Delivered:**
   - `game/core/drifters/base.py` (changed): `DrifterType.UFO`, `Drifter.seeded` (False), `Birth.hazard_speed_mult` (1.0) and `Birth.seed` (None).
   - `game/core/drifters/spawner.py` (changed): `Placement.seed`, `MAX_SEED`, `DEBUG_SPAWNS_SOURCE`, `placement_seed`, the seed refusal (`<type> has no seed`) and the two new `Birth` fields in step 8.
   - `game/core/drifters/ufo.py` (new): `DOME_DRAW_MARGIN`, `ARRIVAL_TOLERANCE_PX`, `UfoTypeExtra`, `ufo_hitbox`, `check_ufo_variant`, `check_ufo_weave`, `weave_stop_distance`, `weave_brake_speed`, `Ufo`.
   - `game/core/drifters/__init__.py` (changed): imports `ufo`.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/drifters/*.py`: clean.
   - `ruff check game` and `ruff format --check game`: no findings. `game/tests/check.sh lint`: pass. `typecheck` (mypy strict): pass.
   - Acceptance smoke, from `game/`, the task's command exactly (run from a file with `PYTHONPATH=.`, same text): prints the twelve expected lines, all matching the task:
     ```
     warning -20.0 300.0 1.974 (12.0, 300.0) 60 96
     660.0 -2.8031 2.272 0.142 42 68
     active 19.48 300.0 False True
     21.45 True True True True True True
     True True True True
     1.5 19.312
     ufo placement needs seed
     ufo placement y 100 is outside its band 188 to 440
     ufo placement needs y
     ufo has no specialty
     meteorite has no seed
     True True True
     ```
     Command: `cd game && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "<the block under Acceptance check in the task>"`.
   - Determinism: ran it twice, `diff` of the two outputs is empty.
   - Contract examples checked by an inline script (not saved): the easing example at y 300 to 220 gives the same velocities and y as the contract table (ticks 1, 2, 16, 17, 50, 51, 52, 64, 65, 66). Level 1 crossing: weaving from n 21, dropped on n 345 with `invert` (x -21.03). Level 8: weaving from n 15, dropped on n 243. 480 runs (2 levels, 40 seeds, 3 start heights, both sides, up to 700 ticks): 0 breaks of the band, of `weave_speed_max` or of the `weave_turn` change cap.
   - Grep of `game/core/` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|random.random(|.mp3|.wav`: the only hits are the substring `.wav` inside `waves.` and `wave_id` in `waves.py`, `wave_files.py` and `run.py`, and the ban list in `game/core/ruff.toml`. No code hit, none in the files I wrote.
   - `game/tests/check.sh`: lint, format, typecheck pass. `core` fails at collection of `tests/core/test_collision.py` (`KeyError: 'hitbox'`, from `ufo.json` having no `hitbox`). With that file ignored, `tests/core`: 744 pass, 3 fail, all the unknown-type cases of `test_wave_files.py` (the list now ends `planet, ufo`). `ui` fails only `test_drifter_registry.py::test_drifter_lists_match_everywhere` (no `ufo` view). All of these are the failures the contract's DRA-104 Impact table names (tasks DRA-104-04, -06 and -03). No other test fails.

4. **Assumptions:**
   - Private helper record `_Weave` (the seven fields one weave step reads and writes) is not in the contract's Interface. It is private, and it exists only for speed: one `replace` of a 35-field drifter costs about 33 us here, and the first version with four per tick cost about 150 us a tick; now about 50 us.
   - Four module constants not named in the Interface, all `Final`, all stand for numbers the contract writes in its rules and are not game values: `PICK_UP_BELOW` (0.5, the first direction draw), `SEED_BITS` (64, the next-seed draw) and `BRAKE_ROUND_DIGITS` (6) in `ufo.py`. In `spawner.py` the default seed width is `MAX_SEED.bit_length()` (32), so no extra constant.
   - `check_ufo_variant` takes `disc_height` as the Interface says but doesn't use it: the check is on the width only.
   - The seed range 0 to `MAX_SEED` is not checked in `spawn_drifter`; the contract puts that at the loaders (the edge).
   - `weave_ticks_left <= 0` (not `== 0`) triggers a pick; the same for every valid tuning (min >= 1), and it can't stick on a bad one.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-104/tasks/DRA-104-01-gameplay-implementer.md`. Left alone, as the task says: `game/core/wave_files.py` (DRA-104-02), the view and `game/app/` (DRA-104-03 and Integration), `game/tuning/drifters/ufo.json` (content, already there), tests. `core/drifters/tuning.py` is unchanged.

7. **Status:** done.

## Decisions
- Update order inside a UFO tick is the contract's (x move, count down or first pick, one ease step, tick count). The ease is the contract's exact rule, not semi-implicit Euler over a force: the contract fixes velocity, then position.
- `weave_brake_speed` finds `k` with a square-root estimate, then corrects it with the contract's own condition (`d <= a (k+1)(k+2)/2`) in two small loops, so the answer is exactly the contract's and no float edge can pick a wrong `k`. At distance 0 it returns 0.0.
- `drawn_parts` walks the hitbox (a box gives its own box, a circle a box of `2 x (r + DOME_DRAW_MARGIN)`), disc first, dome second. It gives the contract's two boxes and keeps `ufo_hitbox` the one place the shape lives. `is_fully_on_screen` is judged on those boxes.
- `Ufo.born` checks in the contract's order: specialty, type values, seed, band. Messages use `g` format. `start_position` raises `ufo placement needs y` before the seed or band checks run, because the spawner calls it first (step 7).
- The spawner's seed refusal sits in step 8, after `start_position`, as the contract orders it. `hazard_speed_mult` is computed once and handed both to `_birth_speed` and to `Birth`.
- Every number comes from the tuning file through `Birth` (`speed_ratio`, entry warning, weave values, band) or from `core.levels` (`HAZARD_SPEED_MULT`, for `check_ufo_weave`). None is set in code beyond the contract's three non-game constants and the three draw constants named above.

## Review fix 2026-10-22: docs/reports/review/DRA-104-01-gameplay-implementer.md
Fixed: DRA-104-01-F1

1. **Task:** Answer the round 1 findings of the review of DRA-104-01 (from the `/implement` skill).

2. **Delivered:** `game/core/drifters/spawner.py` (changed): the speed step now runs before the start step.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes. `py_compile game/core/drifters/*.py`: clean.
   - `ruff check game` and `ruff format --check game`: no findings. `game/tests/check.sh lint` and `typecheck`: pass.
   - Acceptance smoke (the task's command, from `game/`, `PYTHONPATH=.`): the same twelve lines as before. Run twice: `diff` empty.
   - F1 case, inline, not saved: a coin row with `speed` and `seed` now gives `coin has no speed` (it gave `coin has no seed`). A coin with `speed` and no `x` gives `coin has no speed` (it gave `placement needs x`).
   - Grep of `game/core/drifters/` for the banned calls: no hits.

4. **Assumptions:** None new.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-104-01-gameplay-implementer.md`. F2 and F3 ask for no change; left as they are.

7. **Status:** done.

## Decisions
- `_birth_speed` is computed into a local `speed` right after `speed_mult`, before `start_size` and `start_position`, so the refusals run in the contract's order: step 4, step 7, step 8. `Birth` takes the local.

## Answers
DRA-104-01-F1. Fixed: game/core/drifters/spawner.py:129, `speed` computed right after `speed_mult`; passed to `Birth` at `spawner.py:141`.

## Fix 2026-10-22: docs/reports/qa/DRA-104-01-gameplay-implementer.md

1. **Task:** Fix B1 of the QA report: the UFO's y ended a tick up to 7e-14 px outside the band (from QA, via `/implement`).

2. **Delivered:** `game/core/drifters/ufo.py` (changed): `_ease` clamps the new y into `band_top` to `band_bottom` after the arrival snap (line 426); docstring updated.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes. `py_compile game/core/drifters/ufo.py`: clean.
   - `ruff check game`, `ruff format --check game`: no findings. `game/tests/check.sh lint` and `typecheck`: pass.
   - Reproduced first: QA's script printed `449 187.99999999999997 ...` before the fix. After the fix it prints nothing.
   - Wider run, inline, not saved: 199 seeds, 5 start heights, 699 ticks each, Level 1 values: 0 ticks outside 188.0 to 440.0 with no tolerance. `|velocity_y|` never above `weave_speed_max` (1.6) and never changed by more than `weave_turn` (0.1) a tick, with 1e-12 slack on those two asserts only. Run twice: identical output.
   - Acceptance smoke (task command, from `game/`, `PYTHONPATH=.`): the same twelve lines; two runs, `diff` empty.
   - `tests/core` with `test_collision.py` ignored: 744 pass, 3 fail, the same three unknown-type rows of `test_wave_files.py` (task DRA-104-06). No new failure.
   - Grep of `game/core/drifters/` for the banned calls: no hits.

4. **Assumptions:** None new.

5. **Documentation differences:** None. QA's note for the Architect stands: Pick step 5 and Ease don't say how the band edge is kept in float. The clamp works inside the contract as written.

6. **Next:** QA Engineer, bug report `docs/reports/qa/DRA-104-01-gameplay-implementer.md` (B1).

7. **Status:** done.

## Decisions
- The clamp is QA's proposed fix, placed last in `_ease`. Every exact result of the Ease rule is inside the band, so it changes y only by float dust. Velocity is untouched, so the speed and turn limits and the landing on `target_y` are as before.
