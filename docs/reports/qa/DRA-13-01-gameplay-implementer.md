Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-13-01-gameplay-implementer (world scroll and distance counter), Verify mode, requested by the Director.
2. **Delivered:** docs/reports/qa/DRA-13-01-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (9 core, 3 ui tests).
   - Acceptance check run from `game/`: prints `0.0 0` then `110.0 11`. Matches the task.
   - Inline run of 100000 ticks from `start_scroll()`: `ticks == t` and `scrolled_ticks == max(0, t - 30)` on every tick. `meters == scrolled_ticks * 11 // 100` on every tick, never decreasing. `distance_px` never decreases. Input scroll never mutated (the input's `ticks` was `t-1` at each step). Same input twice gives equal output. Assigning to a field raises `FrozenInstanceError`.
   - Boundaries: tick 30 gives 0.0 px, 0 m, no log. Tick 31 gives 1.1 px, 0 m, exactly one line `scroll start tick=31`. 100000 ticks give exactly one log line in total.
   - `SCROLL_PER_TICK == 1.1`, computed from the two constants.
   - `git diff` of `ship.py` and `world.py` shows docstring lines only (5 insertions, 4 deletions, all inside docstrings). Existing ship tests pass.
4. **Assumptions:** None. Inputs were built through `start_scroll()`, as the review advised.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. No open bugs. The `scroll.py` tests are task DRA-13-04 (QA Engineer, Test task mode).
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core PASS · ui PASS
QA: pass
