Verdict: pass
Created by: qa-engineer

1. **Task:** test task DRA-96-07-qa-engineer (the planet and planets in the run), started by the main session.
2. **Delivered:** `game/tests/core/test_planet.py` (new, 11 tests, one per behavior in the task's `## Test` list except the wave loader row), `game/tests/core/test_wave_files.py` (the unknown-type refusal now lists `planet` last, three parametrized rows), `game/tests/CONTEXT.md` (a paragraph for `test_planet.py`; the island paragraph's note on the unknown-type message says `planet` last from DRA-96).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`. `test_planet.py`: 11 passed. `test_wave_files.py`: 177 passed (it failed 3 rows before the edit, as the Impact table expected). The planet file builds its own tuning from the GDD values and reads no `game/tuning/` file. Timeline checked state by state: T+60 ACTIVE and not entered, T+61 entered, T+770 kept (y 630.00), T+771 dropped with `drifter gone id=1 type=planet x=320.00 y=631.10`. Inner rings: the contract's table rows plus the formula as exact `Fraction`s on 361 ticks. A ship 10 px inside the body is hit on tick 1, held by the pull for 181 ticks with the cooldown counting down from 180, hit again on tick 182. No game code was edited.
4. **Assumptions:** The log test expects `invulnerable end` between `life lost lives=2` and `drifter gone` (the run logs it after the hit, 30 ticks later, per run.md Logging). The hit test puts `scroll=STILL` back before each tick so the planet stands where it is while the pull holds the ship.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. No open bug. The wave_check part stays with the main session.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
