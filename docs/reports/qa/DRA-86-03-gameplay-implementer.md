Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-86-03-gameplay-implementer (island block in the ship: `Ground`, `NO_GROUND`, `Ship.against_island`, `spawn_clear`, `block_ship`, the optional `ground` of `step`, the `island contact` log line), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-86-03-gameplay-implementer.md
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core ui)`. Every failure is one the drifters contract's DRA-86 Impact table gives to a later queued task, and none names ship code: typecheck 6 errors, all `tests/core/test_collision.py:589,596` (task DRA-86-07); core 5 failed, 1572 passed (`test_collision.py` guard test and `[floating_island-None]`, task DRA-86-07; three `test_wave_files.py` unknown-type message cases, task DRA-86-09); ui 1 failed, 45 passed (`test_drifter_registry.py`, no `floating_island.json` and no view yet, task DRA-86-06 and the tuning file). Lint and format pass. Every `test_ship*.py` and `test_run*.py` test passes unchanged.
   - Acceptance check reproduced from `game/` (the task's command, `PYTHONPATH=/workspace/game`, SDL dummy). All eight lines match the task:
     ```
     284.0 1.1 True
     0.84 False
     216.0 1.1 True
     384.0 0.0 0.16
     0.0526 0.0197 True
     240.4 1.1 True
     224.0 326.0 True
     True
     ```
   - Edge cases that behave correctly (inline runs, nothing saved):
     - Wall hit and top-line stop on one tick: one `wall hit` line (y after the wall clamp, 11.74) then one `top line stop` line (y 184.00). Matches the review's F1.
     - Island corner at a side wall: ship at x 16 with an island on its right, left push refused, ship goes down to y 316 (the 16 px way out). Same on the right wall at x 624.
     - Upward push that would put the top edge above the top line (168): refused, ship goes down (ground y 197 to 257 gives y 273; ground top 224 gives 208 where up is allowed).
     - `spawn_clear`: tie between up and down with the spot above allowed (island Box(290, 250, 40, 60), foot only) gives 204.0 (above); tie with the spot above past the line (Box(320, 240, 120, 120)) gives 316.0 (below); islands at 330 and 160 leave the spawn alone; 270 gives 194; 210 gives 286; 200 gives 276; `Ground()` and `NO_GROUND` give `spawn()`.
     - Ride, lift off, land: `island contact` logs once at the landing tick (riding 3 ticks logged once), nothing on lift-off ticks, once again on the next landing.
     - Fuzz: 30,000 random steps against 1 to 3 boxes and slopes, each run twice: same result both times, no exception, ship always inside the side walls.
     - Determinism: same ship, thrust and ground twice gives equal ships. Inputs are frozen dataclasses.
   - One edge case fails: see B1. The code does what the contract says. The contract leaves a gap.
4. **Assumptions:** B1 is read as a contract gap and not an implementer bug, because ship.md puts the top line after the islands, which is also the order in 04-ship.md, rule 2, steps 6 and 7.
5. **Documentation differences:** pending approval. 04-ship.md, rule 2, steps 6 and 7 and `docs/contracts/systems/ship.md`, Rules (step 7, Islands) and Presentation ("the ship ... sits on an island's surface, never in it") do not hold when the top-line clamp moves the ship into an island (B1). Proposed change below.
6. **Next:** Architect and Director. Do not send to the Gameplay Implementer or the Integration Engineer until the Director decides B1. If the proposed contract change is approved, the Architect updates ship.md (and the GDD step if the Director wants it), the Gameplay Implementer applies it in `game/core/ship.py`, and QA re-tests this report. Everything else in DRA-86-03 is correct.
7. **Status:** blocked: a contract problem (B1) needs a Director decision.

## Bugs
- **B1 (contract gap, not an implementer bug)** `game/core/ship.py:203-205` (`step`: `block_ship`, then `_stop_at_top_line`), the order set by `docs/contracts/systems/ship.md`, Rules, step 6 "Then islands" then step 7, and 04-ship.md rule 2 steps 6 and 7. Owner if the contract changes: Gameplay Implementer.
  Reproduce (from `game/`, `PYTHONPATH=/workspace/game SDL_VIDEODRIVER=dummy`):
  ```
  python -c "
  from core.collision import Box, deeply_overlaps
  from core.ship import Ground, Ship, Thrust, ship_hitbox, step
  g = Ground(hitbox=(Box(400.0, 255.0, 120.0, 120.0),), velocity_y=1.1)
  r = step(Ship(x=320.0, y=190.0, vx=6.0, vy=-11.0), Thrust(up=True, right=True), g)
  print(r); print(deeply_overlaps(ship_hitbox(r), g.hitbox))
  "
  ```
  Expected: the ship ends clear of the island ("a ship never ends inside an island": ship.md, Presentation, "sits on an island's surface, never in it"; drifters/05-floating-islands.md, rule 4, "moved out ... just to the surface"). Actual: `Ship(x=326.0348, y=184.0, vx=6.0348, vy=0.0, wall=None, at_top_line=True, against_island=False)` and `True`. The ship overlaps the island's top-left corner by about 2.6 px across and 5 px down, with `against_island` False, so no `island contact` is logged on that tick. The next tick pushes it out (to x 324.0, `against_island` True), so the ship is drawn inside the island for one frame.
  Cause: the ship flies up past the top line (here y 190 to 178.74, top edge 162.7). At that spot it is clear of the island, so the block does nothing. The top-line clamp then moves it down to y 184, where its foot reaches 200, past the island's top edge at 195. It needs: the ship rising at 11 px/tick or so (the contract says a climb reaches about 13 px/tick near the top line), sliding sideways at the top line, and an island edge (box corner or slope) between rows 184 and 200 beside it. Six hits in 200,000 random runs with slopes and the sane start (ship clear of the island's previous position, top edge at or below the line, `vy` at least -13). The contract's Rationale (No push through a wall or the top line) already names this kind of clamp-after-push problem for the push, but not for a ship that was clear before the clamp.
  Source of the expected value: ship.md, Presentation and Rationale (Islands block inside the ship step); 04-ship.md, rule 2 step 6; GDD drifters/05-floating-islands.md, rule 4.
  Proposed contract change (Architect to write, Director to approve): in ship.md, Rules, step 7, add that when the top-line clamp moved the ship (`at_top_line` newly True and `y` changed), `step` runs the island block once more on the clamped ship (`block_ship`, the same rules, the same refusals: nothing is pushed up or through a wall, and down is always free), so the returned ship is clear of the ground. `against_island` is True if either pass pushed it, and `island contact` logs once, on the first pass that starts the contact. Update the step flowchart and the `step` Interface line, and the Logging order (wall hit, island contact, top line stop) stays. If the Director wants the order in 04-ship.md, rule 2 kept as written, add a line there that the island block runs again after the top-line clamp. Alternative the Architect may prefer: clamp the top line before the islands and then clamp again after them, with the same effect. The Gameplay Implementer then adds the second `block_ship` call in `step` after `_stop_at_top_line`. It satisfies the contract and the GDD because the ship ends clear of every island and still below the top line, and a ship that was not near the line is unaffected.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (6 errors, `tests/core/test_collision.py`, expected, task DRA-86-07) · core FAIL (5 failed, 1572 passed, expected, tasks DRA-86-07 and DRA-86-09) · ui FAIL (1 failed, 45 passed, expected, task DRA-86-06 and the island tuning file)
QA: fail (typecheck core ui)

## Round 2 2026-10-21

1. **Task:** Re-test of DRA-86-03-gameplay-implementer after the Director's decision on B1, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-86-03-gameplay-implementer.md (this round).
3. **Checks:** No code changed since Round 1 (`git status` shows the same `game/` files). `check.sh` ends `QA: fail (typecheck core ui)`, the same failures as Round 1 and nothing new: typecheck 6 errors, all `tests/core/test_collision.py:589,596` (task DRA-86-07); core 5 failed, 1572 passed (`test_collision.py` guard test and `[floating_island-None]`, task DRA-86-07; three `test_wave_files.py` unknown-type message cases, task DRA-86-09); ui 1 failed, 45 passed (`test_drifter_registry.py`, no `floating_island.json` and no view yet, task DRA-86-06 and the island tuning file). Lint and format pass. No failure names ship code. The Round 1 acceptance check is unchanged because `game/core/ship.py` is unchanged.
4. **Assumptions:** The Director's answer is "Yes, known issue + to-do", given to the question "keep the one-frame overlap as a known issue (written in the QA report and the final summary), and add 'remove the top line block' to your open to-do list for a future scope talk?". The Director plans to remove the top-line block later, which removes the cause. So B1 is no longer judged as a bug or a contract gap in DRA-86, and the Round 1 proposed contract change is withdrawn.
5. **Documentation differences:** None now. The Round 1 request on 04-ship.md rule 2 and ship.md step 7 is withdrawn: no contract or GDD change in DRA-86.
6. **Next:** The verdict stays `blocked`, but not for DRA-86-03. The only failures left are ones a later queued DRA-86 task fixes (DRA-86-06, DRA-86-07, DRA-86-09, and the island tuning file). Re-check this report after those tasks land. The DRA-86-03 code has no open bug and needs no fix. The final summary must repeat the known issue below.
7. **Status:** blocked only by later queued tasks (DRA-86-06, 07, 09 and the island tuning file); nothing is open on DRA-86-03 itself.

## Bugs
- **B1: accepted by the Director, known issue, not an open bug.** `game/core/ship.py:203-205` (`step`: `block_ship`, then `_stop_at_top_line`). When the ship rises fast (about 11 px/tick or more) and slides sideways at the top line, the top-line clamp can move it down into an island's corner or slope for one frame. `against_island` is False on that tick, so no `island contact` is logged, and the next tick pushes the ship out. Reproduce: the Round 1 B1 command, unchanged. Six hits in 200,000 random runs. Decision: kept as is, no fix, no contract change. The Director plans to remove the top-line block in a future scope talk, which removes the cause. To-do: "remove the top line block" is on the Director's open to-do list.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (6 errors, `tests/core/test_collision.py`, expected, task DRA-86-07) · core FAIL (5 failed, 1572 passed, expected, tasks DRA-86-07 and DRA-86-09) · ui FAIL (1 failed, 45 passed, expected, task DRA-86-06 and the island tuning file)
QA: fail (typecheck core ui)

## Round 3 2026-10-21

1. **Task:** Re-test of DRA-86-03-gameplay-implementer after the later queued tasks (DRA-86-06, 07, 08, 09 and the island tuning file) landed, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-86-03-gameplay-implementer.md (this round).
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core and ui all PASS (ui 46 passed). The five core and one ui failures and the six typecheck errors of Round 1 and 2 are gone.
   - No code change in DRA-86-03: `game/core/ship.py` was last modified at 22:14, before the Round 2 report at 22:32. The edge cases of Round 1 stay as they were.
   - Acceptance check re-run from `game/` (the task's command, `PYTHONPATH=/workspace/game`, SDL dummy). All eight lines match the task: `284.0 1.1 True`, `0.84 False`, `216.0 1.1 True`, `384.0 0.0 0.16`, `0.0526 0.0197 True`, `240.4 1.1 True`, `224.0 326.0 True`, `True`.
   - The new `core/test_ship_islands.py` (written by task DRA-86-08 or 09) passes against the ship code, so the island block, `spawn_clear` and the log line are also covered by the harness.
   - B1 reproduced: `Ship(x=326.0348, y=184.0, ..., against_island=False)` and overlap `True`. Same as Round 1. Accepted by the Director as a known issue, so it does not fail the task.
4. **Assumptions:** B1 stays accepted as in Round 2 ("Yes, known issue + to-do"). No fix and no test for it.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer (other DRA-86 QA re-tests run in parallel and are not judged here). The final summary must repeat the B1 known issue.
7. **Status:** done.

## Bugs
- **B1: accepted by the Director, known issue, not an open bug.** Unchanged from Round 2: `game/core/ship.py:203-205`, one-frame overlap after the top-line clamp, the Round 1 command still reproduces it. The Director plans to remove the top-line block in a future scope talk. No other bug is open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (46 passed)
QA: pass
