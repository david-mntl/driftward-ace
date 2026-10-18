Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-61/tasks/DRA-61-01-gameplay-implementer.md`, from the Architect: add `POINTS_PER_METER`, `Run.coin_points` and `Run.score` to `game/core/run.py`.
2. **Delivered:** `game/core/run.py` (changed): `POINTS_PER_METER`, the `coin_points` field, the `score` property, a `start_run` docstring line.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/core/run.py`: clean.
   - `game/tests/check.sh lint` (ruff check and format): pass. `typecheck` (mypy strict): pass, 54 files. `core`: 1334 passed, existing tests unchanged.
   - Acceptance check, run from `game/`:
     ```
     python -c "
     from dataclasses import replace
     from core.run import start_run, step_run
     from core.ship import Thrust
     run = start_run()
     print(run.score, run.coin_points)
     for _ in range(130):
         run = step_run(run, Thrust(up=True))
     print(run.score == run.scroll.meters, run.score)
     print(replace(run, coin_points=50).score)
     "
     ```
     Output:
     ```
     0 0
     True 11
     61
     ```
   - Determinism: the run has no randomness and no clock. The command is a pure function of its inputs, and the output matched on the repeat run.
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: the only hits are the ban messages in `game/core/ruff.toml`. No code hits.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-61/tasks/DRA-61-01-gameplay-implementer.md`. I changed no step of `step_run`, no log line, and no file besides `game/core/run.py`. Coins (DRA-62) are not built: nothing writes `coin_points`.
7. **Status:** done.

## Decisions
- `score` is a property: `self.scroll.meters * POINTS_PER_METER + self.coin_points`. It is never stored, so it freezes at game over and resets on retry because the scroll does (contract, Rules, Score).
- `coin_points` sits after `next_uid`, with default 0, so every existing `Run(...)` keyword call still works.
- `POINTS_PER_METER` = 1. Source: 06-scoring.md, points_per_meter (locked), as the contract's Interface gives it.
- No score log line, per the contract's Logging section.
