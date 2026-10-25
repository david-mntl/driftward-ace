Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-117-02-gameplay-implementer (the graze rule in core: `core/graze.py`, `core/popup.py`, `core/run.py`, Linear DRA-119), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-117-02-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui PASS (ui 46 passed). core: 3160 passed, 1 failed, so the last line is `QA: fail (core)`. The one failure is B1 below.
   - Acceptance check reproduced by the implementation report's script, plus my own inline runs (not saved). A medium meteorite passing the ship's side: OUTSIDE, INSIDE while its zone overlaps, SPENT on the exit tick, one `drifter graze id=1 type=meteorite` line, `grazes` 1, score +25, one GRAZE popup at the ship's center and one ring at age 0; the ring is gone after 15 states, the popup after 60 and rising 0.5 px a tick. A meteorite falling onto the ship: SPENT on the touch tick, a hit, no graze. Protected on the exit tick: no pay, OUTSIDE. Respawn wait: no pay. `GrazeRules(points=40, ring_ticks=5)`: +40, ring gone after 5 states. Game over then retry: `grazes` 0, no rings, no popups, same `graze_rules` object.
   - Edge cases hunted, all correct (a hovering ship fixed in place and a still hazard, so each tick is exact):
     - Two hazards left on one tick: two `drifter graze` lines in uid order, `grazes` +2, score +50, two popups, two rings.
     - Protection boundaries (`invuln_ticks_left` 50 pays on tick 51, 51 does not and leaves OUTSIDE). Exit on the last protected tick: no pay, OUTSIDE; the next clean exit, unprotected, pays once.
     - Entered while invulnerable, left after it ended: pays. Touched while invulnerable (passed through): SPENT, never pays.
     - Re-entering and leaving a spent hazard four times: pays once.
     - Respawn wait: an exit during the wait pays nothing and leaves OUTSIDE; the exit on the press tick that ends the wait pays; a later clean exit after the wait pays once. A touch in the wait is a hit and SPENT.
     - Graze on a fall tick: pays, popup at the fall position (320, 500.5, below the floor), then the life is lost and the ship respawns. Protected fall: no pay, OUTSIDE. Last life, fall plus graze: game over, `grazes` 1, score includes it, and the next tick leaves grazes, popups and rings frozen.
     - Hazard dropped off screen with the ship in its zone: pays on tick 47, the tick of its `drifter gone` line.
     - Electric ball (held still) and chain lightning (pair_flat, held still) with the ship in the 14 px ring: INSIDE from the first firing tick, one pay when it stops firing (tick 240), SPENT after, the next firing (tick 360) never pays.
     - Coin and floating island: `check_grazes` returns the same object in every state, no pay; a run with an island beside the ship has 0 grazes and OUTSIDE.
     - A coin collected, a graze exit and a hit by another hazard on one tick: log order `drifter touch ... effect=collect`, `drifter graze`, `drifter touch ... effect=hit`, `life lost`, `game over`, `drifter gone`; the popups are COIN then GRAZE. On the last life the final score (93) holds the coin and the graze.
     - `popup_ticks` 1, `ring_ticks` 1, `points` 0: popup and ring show on one state and are gone on the next; opacity 1.0 on the first.
     - A meteorite from the spawner (`add_drifters`) put on the ship: OUTSIDE in WARNING (no zone), SPENT and a hit on its first ACTIVE tick, never a graze.
     - Retry with waves: `grazes` 0, no rings, no popups, no drifters, waves restarted, same `graze_rules`. The same inputs twice give equal runs.
     - `start_run()`: default `graze_rules` equal to `DEFAULT_GRAZE_RULES`, `grazes` 0, score 0.
4. **Assumptions:**
   - B1 is the case `docs/contracts/DRA-117/impact.md` hands to QA (last paragraph): it is reported against the "Failures expected" table and DRA-117-05 changes the test. I did not edit any test (Verify mode saves nothing in `game/tests/`).
   - The game code is correct for B1; the test compared a touched UFO with an untouched twin and now differs on `graze_state` only, as `run.md` step 5b.3 sets.
5. **Documentation differences:** None.
6. **Next:** The only open item is B1, a test-side failure. The Architect's task DRA-117-05 (`docs/contracts/DRA-117/tasks/DRA-117-05-qa-engineer.md`, "Builds": any existing core test that `impact.md` lets fail) brings the test in line, so no Gameplay Implementer fix is needed. Per the Director's rule that a failure only a queued later task fixes does not stop the build, the Integration Engineer's step waits for DRA-117-05; the code of DRA-117-02 has no open bug. Re-test after DRA-117-05 lands.
7. **Status:** done.

## Bugs
- **B1** `game/tests/core/test_ufo.py:1324`, owner: QA, through task DRA-117-05 (not game code). Reproduce: `game/tests/check.sh core -k test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`.
  Expected: the test passes. Actual: `assert replace(after, rehit_ticks_left=0, uid=0) == replace(twin, uid=0)` fails on `graze_state`: the touched UFO is `SPENT`, the untouched twin is `OUTSIDE`.
  Source: `docs/contracts/systems/run.md`, Rules, step 5b.3 (a touch sets SPENT); `docs/contracts/DRA-117/impact.md`, "Failures expected", last paragraph (a whole-drifter compare that turns up is brought in line by DRA-117-05).
  Proposed fix: in that compare, also set `graze_state` to `GrazeState.OUTSIDE` on the touched UFO, `replace(after, rehit_ticks_left=0, uid=0, graze_state=GrazeState.OUTSIDE) == replace(twin, uid=0)`, and add one assertion that `after.graze_state is GrazeState.SPENT`. That keeps the test's point (the UFO keeps flying and weaving as an untouched one) and checks the new fact.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3160 passed, 1 failed: B1) · ui PASS (46 passed)
QA: fail (core)

## Round 1 2026-10-25

1. **Task:** Re-test of DRA-117-02-gameplay-implementer after B1 (the stale `test_ufo.py` compare) was fixed on the test side by QA task DRA-117-05. No implementer fix was made. Started by /implement.
2. **Delivered:** docs/reports/qa/DRA-117-02-gameplay-implementer.md (this round appended).
3. **Checks:**
   - B1 reproduce command `game/tests/check.sh core -k test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`: 1 passed.
   - Read the changed test (`game/tests/core/test_ufo.py:1324-1328`): it asserts `after.graze_state is GrazeState.SPENT` on every tick, then compares the touched UFO with its untouched twin with `graze_state` set to the twin's. That is the fix I proposed, and it keeps the test's point (the UFO keeps flying and weaving).
   - Full `game/tests/check.sh`: every step PASS, core 3231 passed (it was 3160 passed and 1 failed in round 0; new tests from DRA-117-05 to -07 account for the rest), ui 65 passed. Last line `QA: pass`.
   - The game code was not changed for B1, so my round 0 edge-case runs of the graze rule still stand.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. No bug is open on DRA-117-02.
7. **Status:** done.

## Bugs (round 1)
- **B1** fixed. `game/tests/core/test_ufo.py:1324`: the test now passes and also asserts the touched UFO is SPENT. No new bug.

## Harness (round 1)
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3231 passed) · ui PASS (65 passed)
QA: pass
