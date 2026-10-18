Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of task `DRA-61-01-gameplay-implementer` (`POINTS_PER_METER`, `Run.coin_points`, `Run.score`), requested through `/implement`.
2. **Delivered:** `docs/reports/review/DRA-61-01-gameplay-implementer.md` (this file). Reviewed: `game/core/run.py`.
3. **Checks:** Read `game/core/run.py` against `docs/contracts/systems/run.md` (Purpose, Diagram, Interface, Rules: Values, Score, Logging; Impact DRA-61; Rationale DRA-61), `docs/design/gdd/06-scoring.md`, `game/core/scroll.py` (`meters` is `int`, floored), `game/CONTEXT.md`, `game/ruff.toml` and `game/core/ruff.toml`. Traced the acceptance check by hand: 130 ticks, 30 still, 100 scrolled at 1.1 px = 110 px = 11 m, so `0 0`, `True 11`, `61` follow from the code. Grepped `game/` for `score`, `coin_points`, `POINTS_PER_METER`: only `game/core/run.py` uses them; nothing writes `coin_points`. New lines are under the 100-character limit. Nothing run.
4. **Assumptions:** The grazes left out of the formula are a scope limit (scope report DRA-61, cited in contract Rules, Score), not a contract-GDD conflict.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, tasks `DRA-61-04-qa-engineer` and `DRA-61-05-qa-engineer`. Open findings: 0 must-fix, 0 should-fix, 0 note.
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
- Lose the last life: `score` on the game-over tick equals `game over meters=%d`, and stays the same on every frozen tick after.
- Retry after game over: `score` and `coin_points` are 0 on the retry tick.
- Fall, respawn wait and hit with lives left: the score keeps counting with the meters and never drops.
- `replace(run, coin_points=n).score == run.scroll.meters + n`; `run.level` doesn't change with `coin_points`.
- Existing `Run(...)` keyword builds in `test_run.py`, `test_run_drifters.py`, `test_chain_lightning.py`, `test_fireball.py` still pass unchanged.
