Status: reviewed
Created by: implementation-reviewer

1. **Task:** review `docs/reports/implementation/gameplay/DRA-96-01-gameplay-implementer.md` (the planet pull in the ship step), passed by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-96-01-gameplay-implementer.md` (this file). Reviewed: `game/core/ship.py`.
3. **Checks:** read the code against `docs/contracts/systems/ship.md` (Interface, Rules: Values, step 2, Planet pull, Escape, Other rules, Logging; Impact; Rationale), the task file `docs/contracts/DRA-96/tasks/DRA-96-01-gameplay-implementer.md`, `docs/design/gdd/drifters/08-planet.md` (rules 4, 5, Edge cases), `docs/design/gdd/04-ship.md` (rules 2, 5), `game/CONTEXT.md` and `game/ruff.toml`. Worked the twelve expected acceptance lines by hand against the code: all match (for example 280 → 0.2 × 30/118 + 0.16 = 0.210847; (229, 400) → 0.1 × 0.94 = 0.094). Ran nothing.
4. **Assumptions:** none. `git status` shows only `game/core/ship.py` changed in `game/`, so I took that file as the full delivery.
5. **Documentation differences:** None. The contract agrees with 08-planet.md and 04-ship.md on the pull shape, the place in the tick order, the cap at `pull_max` and the strict escape bound.
6. **Next:** QA Engineer, task DRA-96-05 (`game/tests/core/test_ship_pull.py`). See For QA below.
7. **Status:** done.

## Findings
None.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- Escape check at the exact tie: `pull_max + GRAVITY` is a float sum, so a value that ties 0.42 on paper (0.26) may not tie in binary. Test strictness with values that are exact in binary, or patch the constants.
- Escape check reads the constants at call time (`game/core/ship.py:249`): patch `GRAVITY` or `THRUST_UP` and confirm the result changes.
- Ship inside the surface and at the exact center: the pull stays at `pull_max`, and is 0 at the center (`game/core/ship.py:223`, `:236`).
- Pull plus the fall cap: a ship at `FALL_CAP` inside a field still caps at 5.5 (`game/core/ship.py:393`).
- Existing ship, island and run tests must pass unchanged with `wells` left out.
