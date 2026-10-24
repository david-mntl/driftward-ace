Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** DRA-96-03, from the Architect: `gravity_wells` and step 4 passing the wells to the ship step, in `game/core/run.py`.
2. **Delivered:** `game/core/run.py` (changed): `gravity_wells(drifters)`, step 4 calls `step(run.ship, thrust, ground, wells)`, imports `GravityWell`. `block_ship` gets no wells, so a waiting ship is never pulled.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/run.py`: clean.
   - `ruff check game` and `ruff format --check game`: clean. `game/tests/check.sh lint`: pass.
   - Smoke run, the task's acceptance command from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "..."`. Output:
     ```
     0.26
     309.0 0.0 True
     -0.16
     0.26
     (GravityWell(x=320.0, y=400.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2),) ()
     ```
     All five lines match the task.
   - Determinism: ran the smoke twice, output identical.
   - Grep of `game/core/run.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|random.random(|.mp3|.wav`: no hits (the only matches are `self.waves` names, which are not `.wav`).
   - `check.sh typecheck`: pass (74 files).
   - `check.sh core`: collection error in `test_collision.py` (`KeyError: 'hitbox'` reading `planet.json`) and, with that file ignored, 3 failures in `test_wave_files.py` (the unknown-type message gains `planet`). Both are in the drifters contract's DRA-96 Impact table (tasks DRA-96-06 and DRA-96-07). The other 504 core tests pass, so every existing run test passes unchanged.
   - `check.sh ui`: one failure, `test_drifter_registry.py` (no `planet` view yet, task DRA-96-04). Expected per the Impact table.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-96/tasks/DRA-96-03-gameplay-implementer.md`. Left alone: `game/core/ship.py` and the drifters files (tasks 01 and 02), `game/tuning/drifters/planet.json`, tests, `game/app/`.
7. **Status:** done.

## Decisions
- Wells are gathered after step 3, from the updated drifters, so they sit where the planets are on the state after the tick. Source: run.md, Rules, step 4.
- `gravity_wells` returns the tuple built from `gravity_well()`; an empty tuple equals `NO_WELLS`, so no separate branch. The run never tests for a planet type. Source: run.md, Interface and Rationale (DRA-96).
- The wells are computed every playing tick but only passed to `step`, not `block_ship`: that is what keeps the respawn wait free of pull. The press tick steps the ship, so the pull starts with gravity. Source: run.md, step 4.
- No number added. No log line added: the pull logs nothing. Source: run.md, Logging.
