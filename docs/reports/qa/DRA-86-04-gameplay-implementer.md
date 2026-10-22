Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-86-04-gameplay-implementer (the islands in `core.run`: `island_ground`, steps 4 and 6, the `respawn clear of island` line), started by /implement. Review is `reviewed`; F1 fixed.
2. **Delivered:** docs/reports/qa/DRA-86-04-gameplay-implementer.md
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core ui)`, so it can't be `pass`. Every failure is one the drifters contract's DRA-86 Impact table gives to a later queued task, and none comes from `game/core/run.py`: typecheck 6 errors, all `tests/core/test_collision.py:589,596` (task DRA-86-07); core 5 failed, 1572 passed (`test_collision.py` guard test and `[floating_island-None]`, task DRA-86-07; three `test_wave_files.py` unknown-type message cases, task DRA-86-09); ui 1 failed, 45 passed (`test_drifter_registry.py`, no `floating_island.json` and no view yet, task DRA-86-06 and the tuning file). Lint and format pass. Every `test_run*.py`, `test_coin.py`, `test_fireball.py`, `test_chain_lightning.py` and `test_ship*.py` test passes unchanged. The failure list is identical to the DRA-86-02 and DRA-86-03 rounds.
   - Acceptance check reproduced from `game/` (the task's command, `PYTHONPATH=.`, SDL dummy drivers, run twice, identical):
     ```
     254.0 True 3
     326.0 True 2
     241.2 True 1.1
     1 1.1 True
     ```
   - Edge cases that behave correctly (inline runs, nothing saved):
     - Fall onto a box that covers the respawn point, not protected: ship at 326.0, `waiting` True, lives 2, log order `life lost`, `respawn from`, `respawn clear of island y=326.00`. Protected: same spot, `waiting` False, lives 3, invuln keeps counting (49 from 50), `respawn from` then `respawn clear of island`. No island: spawn (240.0), no `respawn clear of island` line.
     - Last life fall with an island on the respawn point: game over, ship stays where it fell (y 500.5), no clear line.
     - Ship in the respawn wait under an island, no press: carried down at 1.1 px/tick, stays waiting, logs `island contact` once. Carried off the floor while protected (scroll already moving): respawn, `waiting` False, no life lost, one `respawn from` line. Carried off the floor unprotected: life lost, respawn waiting.
     - Press on the tick the wait ends under an island: `waiting` False, ship stepped (vy -0.26), no crash.
     - Waiting ship overlapping a box from the side: pushed out to the top (y 224.0), still waiting, no life lost.
     - Stack of boxes pushing the respawn spot past the floor: spot y 556.0, next tick falls again (protected: no life; the spot repeats, per the contract's note).
     - Island with a coin and a meteorite on the ship: the coin pays (50) and a hazard hit costs one life as before; no `drifter touch` line names the island. Ship riding an island 60 ticks: lives 3, no touch line, no points.
     - `island_ground`: a WARNING island and a GONE island add no shape; empty input gives `NO_GROUND` itself.
     - Game over tick: `step_run` ignores the ground (the retry rule is untouched).
     - Fuzz: 30 seeds of 600 ticks with random islands, thrust and retries, each run twice: identical results, ship always inside the side walls, no exception.
   - Known issue not reopened: DRA-86-03 B1 (one-frame overlap after the top-line clamp), accepted by the Director.
4. **Assumptions:** Verdict is `blocked`, as for DRA-86-01 to 03, because `check.sh` can't end `QA: pass` until the later queued tasks land. It is not a contract problem and no bug is open against `run.py`. Re-test after DRA-86-06, 07, 09 and the island tuning file.
5. **Documentation differences:** None.
6. **Next:** `/implement` continues with DRA-86-05 and the later tasks (DRA-86-06 view and tuning file, DRA-86-07 and 09 test updates). Re-run `check.sh` after them; if it ends `QA: pass`, this task needs no further change. No fix owed by the Gameplay Implementer.
7. **Status:** blocked: only because the harness fails on files owned by later queued tasks. Nothing in `game/core/run.py` is wrong.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (6 errors, `test_collision.py`, DRA-86-07) · core FAIL (5 failed, 1572 passed; DRA-86-07 and DRA-86-09) · ui FAIL (1 failed, 45 passed; DRA-86-06 and the tuning file)
QA: fail (typecheck core ui)

## Round 2 2026-10-21

Verdict at the end of this round: pass

1. **Task:** re-test of DRA-86-04-gameplay-implementer after the later queued tasks (DRA-86-06, 07, 08, 09 and the island tuning file) landed. No code changed in this task. Started by /implement.
2. **Delivered:** this round in docs/reports/qa/DRA-86-04-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck, core and ui all PASS (ui 46 passed). Last line `QA: pass`. The five core failures, six typecheck errors and one ui failure of round 1 are gone.
   - Acceptance check re-run from `game/` (the task's command, `PYTHONPATH=.`, SDL dummy drivers, twice, identical):
     ```
     254.0 True 3
     326.0 True 2
     241.2 True 1.1
     1 1.1 True
     ```
   - `game/core/run.py` is unchanged since round 1, so the round 1 edge cases (respawn under an island, last-life fall, carried wait, press on the wait's last tick, box stack past the floor, coin and meteorite on an island, game-over tick, 30-seed fuzz) still stand. The tests added by DRA-86-07 to 09 (`test_ship_islands.py`, `test_floating_island.py`, the island cases in `test_collision.py`) now cover the run rules and pass.
   - Known issue not reopened: DRA-86-03 B1 (one-frame overlap after the top-line clamp), accepted by the Director.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, if every other DRA-86 task is clear.
7. **Status:** done.

## Bugs
None open. (Round 1 had none; the block was the harness only, now cleared.)

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (46 passed)
QA: pass
