Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-96-01-gameplay-implementer (planet pull in the ship step), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-96-01-gameplay-implementer.md. No test files (Verify saves none; `test_ship_pull.py` is task DRA-96-05).
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass` (46 passed; existing ship, island and run tests pass unchanged with `wells` left out).
   - Acceptance check from the task file, run inline headless: all twelve lines match the task's expected output. `250.0 0.0 0.16`, `280.0 0.0 0.210847`, `309.0 0.0 0.26`, `368.0 0.0 0.36`, `390.0 0.0 0.36`, `400.0 0.0 0.16`, `0.094 0.16`, `-0.06`, `0.1 0.1`, `True`, `0.2 accepted`, then `pull_max is too strong: pull_max + gravity must stay below thrust_up (0.3 + 0.16 >= 0.42)`.
   - Edge cases, all correct: left held at (288, 400) gives vx -0.2068 (contract table); ship at `vy` 5.5 and 5.4 inside the field still caps at 5.5; pull magnitude is exactly 0.2 at d 5, 28.28 and 0.001 (never above `pull_max`); at d 32 the pull is 0.2, just past it slightly less; at d 150 it is 0 and at d 149.999 it is about 1.7e-6; the exact center gives (0, 0); an empty `wells` gives (0, 0); two identical wells add up; the input ship is not mutated; `wells` passed positionally (4th argument) equals the keyword call; same inputs twice give identical results.
   - Escape check reads constants at call time: patching `GRAVITY` to 0.1 and `THRUST_UP` to 0.5 changes the verdict. Exact binary ties (0.25 + 0.25 >= 0.5, and `pull_max` 0.25 >= `thrust_side` 0.25) are refused (strict). Up check comes first when both rules are broken. The 0.32 + 0.1 float tie (the review's note) is refused, as the contract's "below is strict" implies.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer on this task's pass; the later tasks (DRA-96-02, -03, -05) are unaffected.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
