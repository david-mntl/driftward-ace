Verdict: pass
Created by: qa-engineer

1. **Task:** `docs/contracts/DRA-76/tasks/DRA-76-09-qa-engineer.md` (Architect): tests for the waves inside the run (`core.run`).
2. **Delivered:** `game/tests/core/test_run_waves.py` (new, 9 tests) and `game/tests/CONTEXT.md` (a paragraph for `core/test_run_waves.py`).
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`. `test_run_waves.py` is in the `core` step (1576 passed); every earlier test is unchanged and still passes.
   - One test per behavior in the task's `## Test` list. The list's fifth item holds three behaviors (the freeze, the retry's new seed, the same seed again), so it has three tests.
     1. No waves: Level 1, nothing due, 1.1 px a tick on every tick for 70 ticks, a retry with no waves, only `new run` logged.
     2. With waves: level and due placements come from the waves, at every level 1 to 8. The wave clock steps once on the wait, the press that ends it, protected ticks, a fall, a protected fall and the tick lives reach 0 by a fall and by a hit. A rest of 3 ticks shows a skipped or doubled step.
     3. The level-up tick (tick 50) moves 1.1 px and tick 51 moves 1.21 px. A parked coin moves in step 3 by exactly what step 5 scrolls, on 70 ticks. A run at each level 1 to 8 moves at that level's speed. Distances are summed from exact fractions.
     4. Drifters added after the level-up tick are born at Level 2 (hazard speed × 1.06). `as_level` wins, and a drifter added before keeps its Level 1 speed for the next ticks. A wave placement due on the level-up tick is born at Level 2.
     5. Game over freezes the waves, the scroll and the ship under held, changed and released arrows. A retry gives Wave 0, Level 1, no spawn, a seed from the first run's seed, and picks that match a replay of that seed. A third run draws from the second's seed. The same seed run twice, with a retry, gives identical states; a different seed does not (`determinism`).
     6. Logs: a retry tick logs `new run` then `wave start id=w0 level=1 random=False`. A level-up tick with a fall and a drop logs the run's lines, then `wave end`, `level up`, `wave start`. The same on the last life logs `game over meters=2` before the waves' lines.
   - Mutation check on a scratch copy of `game/` (not saved here). Each change was caught by the test named: step 3 reading Level 1 (test 3), step 5 using the raised level (test 3), no wave step during the wait (test 2), no wave step on the game-over tick (test 2), a retry that keeps the old seed (the retry test), `add_drifters` at Level 1 (test 4), a wave step on frozen ticks (the freeze test).
   - A first run of the file failed on a test mistake (an up arrow slows the fall, so the run did not end). That was my test, not a bug in game code. Fixed in the file. No bug in game code found.
4. **Assumptions:** The first and second seeds are `20261019` and the one drawn from it, as the contract's Seeds rules say. The test books are built in code, with waves that are 11 px long so the level changes within 50 ticks. The wave placements are meteorites at `y=-20`; the test books never go through the loader.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The app's `add_drifters` call, the debug choice and the browser run are checked at integration, as the task says.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
