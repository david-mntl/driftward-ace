Verdict: pass
Created by: qa-engineer

1. **Task:** QA test task `docs/contracts/DRA-86/tasks/DRA-86-08-qa-engineer.md`, started by /implement: the ship against floating islands (`Ground`, `NO_GROUND`, `against_island`, the islands in `step`, `block_ship`, `spawn_clear`, the `island contact` log line).
2. **Delivered:**
   - `game/tests/core/test_ship_islands.py` (new): 122 test cases, 30 test functions, one per behavior of the task's `## Test` list (several parametrized).
   - `game/tests/CONTEXT.md` (changed: a paragraph for the new file, before the `test_drifters.py` one).
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui PASS. `core`: 2794 passed, 3 failed. All 122 cases of `test_ship_islands.py` pass against the code. The 3 failures are the `test_wave_files.py` unknown-type refusals the task's Acceptance check names as left until DRA-86-09 (B1, filed in `docs/reports/qa/DRA-86-07-qa-engineer.md`, still open).
   - Behaviors covered, task line by line: pushed out of every variant and `invert` from above, below, left and right (straight faces of every box, the triangle's flat sides) and off the triangle's slope, exactly to the surface (touching, other coordinate and speed unchanged, clear of the island); speed into the surface dropped against a still ground and two moving grounds, into, none and away, plus the slope; standing on a rectangle moving 1.1 for 120 ticks (tick 1 is the Diagram's 284.00 and vy 1.10), sliding along it, lifting off with up thrust; held under an underside for 100 ticks (tick 1 is 216.00, vy 1.10, never above 1.10), side thrust sliding out, no thrust falling away (vy 1.10 + 0.16 n); the slope slide for 20 ticks (tick 1 is vx 0.0526, vy 0.0197); wall refusal (left and right), top-line refusal (the next shortest way is a side, then down, and a top edge exactly on the line is allowed, one px past is refused), down always left (two islands covering x 0 to 640); ties (all four equal, down over left, left over right, a 3e-10 hair short still up, a 1e-6 shorter down wins); one push out of the L, the T and two overlapping islands, clear of all; no ground (5 kinds of empty or distant ground, 60 states, 16 thrusts, the pre-DRA-86 step written in the file) and edge touches with `against_island` False; `block_ship` alone at rest for every variant; `spawn_clear` (the Diagram's table, touching on four sides, above, below, top-line limit at 168 and 167, tie, nearer below, at rest); `island contact` once per contact by `step` (ride, lift off, land again) and by `block_ship`, and the order `wall hit`, `island contact`, `top line stop` in one step.
   - Not vacuous: 13 mutations of a copy of `game/core/ship.py` (under the scratchpad, never the repo). 11 were caught: ties without the tolerance, ties favouring the later way, walls ignored, top line ignored, speed measured against a still ground, a bounce, `island contact` logged every tick, `against_island` not reset, spawn below on a tie, spawn ignoring the top line, no speed drop. Two survived and are not gaps: "touching holds the ship" is the same result as the strict overlap (touching is not an overlap either way), and one was a no-op edit.
   - Same inputs twice give the same ships: every test is pure and repeatable; no randomness.
4. **Assumptions:**
   - The triangle has no face on its right, only the slope, so "from the right" for the triangle is the slope test. The island's own right face is tested for every other shape.
   - The ties and walls are tested on 120 x 120 and 320 x 120 boxes written from the Diagram's numbers, not the file, so a tuning change does not move them. The per-variant push-out reads the file.
   - The one-frame overlap after the top-line clamp (DRA-86-03, QA B1) is not tested, as the Director accepted it as a known issue.
5. **Documentation differences:** pending approval, does not block this task. `docs/contracts/systems/ship.md`, Diagram, Islands, Slope, says "the foot's lower right corner is 0.16 down, 0.1498 deep along n". On the upright triangle the corner that meets the slope is the foot's lower **left** corner (the slope rises to the left, so the left corner is the deepest along `-n`). Check: with the lower right corner on the line, `block_ship` still pushes the ship out, because the lower left corner is then inside the island. The numbers in that line (0.16, 0.1498, (0.0526, 0.0197)) are right and the code is right. Proposed change: replace "lower right corner" with "lower left corner". The tests find the corner from the ship's boxes (`deepest_corner`) and do not depend on the wording.
6. **Next:** QA Engineer, task `DRA-86-09-qa-engineer.md`: it fixes the three `test_wave_files.py` cases (B1 of the DRA-86-07 report), after which `check.sh` should end `QA: pass`. Director: approve or reject the one-word contract change in item 5 (Architect applies it). Then the Integration Engineer.
7. **Status:** done.

## Bugs
- **B1 (not new, filed in DRA-86-07, owner QA Engineer, task DRA-86-09)** `game/tests/core/test_wave_files.py`. Reproduce: `game/tests/check.sh core -k wave_files`. Expected: the unknown-type refusal lists `floating_island` (drifters.md, Impact). Actual: 3 cases (`placement type 'ufo'`, `'Meteorite'`, `''`) still expect the old list. Proposed fix: update those three `Refusal` prefixes in DRA-86-09. This is the one failure the Acceptance check of this task leaves open. No bug in `game/core/ship.py` was found.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3 failed in `test_wave_files.py`, 2794 passed; `test_ship_islands.py` 122 passed) · ui PASS
QA: fail (core)

## Round 2 2026-10-21

1. **Task:** Re-test of this report after task DRA-86-09 fixed B1 (the three `test_wave_files.py` unknown-type rows), started by /implement.
2. **Delivered:** this appended round. No test file changed in this round.
3. **Checks:**
   - B1 reproduce: `game/tests/check.sh core -k "wave_files and (ufo or Meteorite or unknown)"`: 8 passed. The expected list at `game/tests/core/test_wave_files.py:359` ends `floating_island`, as drifters.md (Impact) says.
   - Neighbor: `game/tests/check.sh core -k ship_islands`: 122 passed (the whole of `test_ship_islands.py`, unchanged).
   - `game/tests/check.sh` (all steps): ends `QA: pass`.
4. **Assumptions:** none new. The one-frame overlap after the top-line clamp (DRA-86-03 B1) stays untested, as the Director accepted it as a known issue.
5. **Documentation differences:** pending approval, does not block. The `docs/contracts/systems/ship.md` wording "lower right corner" (Diagram, Islands, Slope) should read "lower left corner" (round 1, item 5). The Director decides; the Architect applies it.
6. **Next:** Integration Engineer.
7. **Status:** done.

## Bugs
- **B1** fixed. The three `test_wave_files.py` unknown-type rows now expect the list ending `floating_island`; they pass.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
