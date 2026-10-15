Verdict: pass
Created by: qa-engineer

1. **Task:** test task DRA-29-08 (objects inside the run: entry, hits, one hit per hazard, leaving), docs/contracts/DRA-29/tasks/DRA-29-08-qa-engineer.md, from the Architect.
2. **Delivered:** game/tests/core/test_run_objects.py (13 tests, one per item 1 to 13 of the task). Report: docs/reports/qa/DRA-29-08-qa-engineer.md.
3. **Checks:** check.sh ends `QA: pass`. The core step collects 65 tests, 13 of them new, all passing; `tests/core/test_run.py` and `tests/core/test_ship.py` are untouched and still pass. Expected values are typed in the test from the GDD (source on each constant); nothing is imported from the code under test to compute an expected value, and `game/tuning/` is never read. Tuning records are built in the test. Guard check: I ran the new tests against throwaway mutated copies of `game/` (in the scratchpad, `game/` itself untouched). Each mutation failed the named tests: `may_hit_ship` always True (hits once), hit while protected (invulnerable test and log test), hit tested after a fall (fall-only test), `add_objects` at game over (add_objects and last-life tests). Edge cases covered: first and last warning state, a warning that ends on an overlapping tick hits that tick, the full 30 protected ticks then a hit on the 31st, the drop on exactly the tick the top edge reaches y 480, a rock at y -200 never dropped, a hit during the respawn wait, a fall plus a touch on both a non-last and the last life, 100 frozen ticks after game over, the log order on a two-rock hit tick.
4. **Assumptions:** the game-over ship is compared with the ship of the same tick with no object (the contract says it stays where it was hit). To keep a ship under a falling rock through many ticks, tests put it back at (320, 240) with `replace` between steps. The ship-beside-the-rock case uses a rock at (345, 232) and the test checks the graze zone reaches the ship while the hitbox doesn't. Item 12 also checks the new run equals `start_run()` with `held` set. No marker is used: the tests are short, not smoke or determinism runs.
5. **Documentation differences:** None.
6. **Next:** Architect closes task DRA-29-08 (it stays `Status: open`). No bugs. No change to `game/tests/CONTEXT.md`: no new fixture, folder or convention. Task DRA-29-09 can proceed.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (65 passed) · ui PASS (11 passed)
QA: pass
