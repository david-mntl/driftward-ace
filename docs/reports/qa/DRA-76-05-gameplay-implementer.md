Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-76-05-gameplay-implementer (the run's waves in `core/run.py`, `level_at` and `LEVEL_STARTS_M` removed), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-76-05-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass` (46 tests; env, lint, format, typecheck, core, ui all PASS).
   - Acceptance check, run from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=.`. Output matches the task's four lines:
     ```
     1 None ()
     1 w0 ['coin']
     51 2 p 23.21 (1, 0, 0, 0, 0, 0, 0)
     1 w0 True 0
     ```
     Run twice, identical (same md5 of the output).
   - Level rise tick (inline run): the scroll moves 0.0 on ticks 1 to 30 and 1.1 px on ticks 31 to 50 (tick 50 is the rise tick, `run.level` 2 after it). Tick 51 and on move 1.21 px. A parked coin added on tick 49 moves 1.1, 1.21, 1.21, 1.21, the same as the world each tick (steps 3 and 5 agree). `add_drifters` after the rise logs `level=2`.
   - Lives reach 0 on the tick Wave 0 ends: step 9a still runs (`game over`, then `wave end id=w0`, `wave start id=p0`; `core.waves` lines come after the `core.run` ones, as the log-order rule says). The next tick changes nothing: waves and scroll equal, no log lines.
   - Retry: logs `new run` (core.run), then `wave start id=w0 level=1 random=False` (core.waves). The new run has Level 1, Wave 0, scroll ticks 0, no drifters or popups, 3 lives, score 0, `held` = the retry thrust, a seed different from the old one, `wave_spawns_due` `()`. Retry chain from seed 3 gives the same three seeds twice, and seed 4 gives different ones. A run with no waves retries to `waves` None, level 1.
   - Respawn wait (protected, 45 ticks): the wave clock ran, Wave 0 ended on tick 40 and the pool wave started. A protected fall on the level-rise tick: no life lost, waves stepped, `level up level=2` logged.
   - Run with no waves vs a run with waves over 300 ticks of the same thrust: identical ship, lives and game-over state while at Level 1.
   - Long soak: 6000 ticks, a 7 px wave book with 3 pool waves, game overs and retries in the middle. Level 8 reached, no error. Same seed twice gave an identical state sequence and identical log lines; a different seed gave a different sequence.
   - Grep of `game/` and `tools/` for `level_at` and `LEVEL_STARTS_M`: no code hit.
   - Review F1 (docstring "no randomness"): `run.py` draws nothing, still true of this file; not a QA matter.
4. **Assumptions:** On a frozen game-over tick `run.wave_spawns_due` keeps the placements due on the tick the run ended. The contract says the waves do not change on a game-over tick, so this follows it, and `add_drifters` returns the run unchanged at game over, so nothing spawns. Not listed as a bug.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The app still has to call `start_run(waves)` and `add_drifters(run, run.wave_spawns_due, ...)` (task DRA-76-05 report, Next).
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
