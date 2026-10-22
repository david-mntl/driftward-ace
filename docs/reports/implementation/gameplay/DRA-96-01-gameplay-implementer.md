Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-96/tasks/DRA-96-01-gameplay-implementer.md`: add the planet pull to the ship (from the Architect).
2. **Delivered:** `game/core/ship.py` (changed): `GravityWell`, `NO_WELLS`, `well_pull`, `check_escapable_pull`, the `wells` argument of `step`, the pull in step 2 (`_accelerate`), the module docstring.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes. `python -m py_compile game/core/ship.py`: clean.
   - `ruff check game`: all passed. `ruff format --check game`: 77 files formatted. `game/tests/check.sh`: `QA: pass` (env, lint, format, typecheck, core, ui). Every existing ship and run test passes unchanged.
   - Acceptance command, run from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -c "<the command in the task file, verbatim>"`. Output, twelve lines, as the task expects:
     ```
     250.0 0.0 0.16
     280.0 0.0 0.210847
     309.0 0.0 0.26
     368.0 0.0 0.36
     390.0 0.0 0.36
     400.0 0.0 0.16
     0.094 0.16
     -0.06
     0.1 0.1
     True
     0.2 accepted
     pull_max is too strong: pull_max + gravity must stay below thrust_up (0.3 + 0.16 >= 0.42)
     ```
   - Determinism: ran it twice, outputs identical.
   - Grep of `game/core/ship.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no hits.
4. **Assumptions:** None. Messages follow the contract's f-strings; `:g` gives `0.3`, `0.16`, `0.42` as the task shows.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-96/tasks/DRA-96-01-gameplay-implementer.md`. Left alone: `game/core/run.py` (DRA-96-03), the planet drifter (DRA-96-02), `game/app/tuning.py` (the loader's call to `check_escapable_pull`).
7. **Status:** done.

## Decisions
- Pull measured from the ship as it came into `step`, then added after gravity and before drag and the fall cap: `_accelerate` takes the pull as a fourth argument, so the step order stays in one function. Source: systems/ship.md, Rules, step 2.
- `well_pull` skips a well at `d >= pull_radius` and at `d == 0.0`; `_pull_strength` returns `pull_max` at or inside the surface and the straight line otherwise, so the pull never exceeds `pull_max`. Source: systems/ship.md, Planet pull, rules 2 to 5.
- `check_escapable_pull` reads `GRAVITY`, `THRUST_UP` and `THRUST_SIDE` at call time, strict comparison, up check first. Source: systems/ship.md, Escape.
- No new game value and no logging. The only new import is `math`. `wells` defaults to `NO_WELLS`, so old calls give the same ship.
