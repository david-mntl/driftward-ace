Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-19-02-ui-developer (debug overlay shows `0.00`, never `-0.00`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-19-02-ui-developer.md
3. **Checks:** check.sh ends `QA: pass`. Acceptance check run headless from `game/` with the Ship from the task. The rendered strings, captured from `font.render`, are `x 300.00`, `y 184.00`, `vx 0.00`, `vy -0.26`. The PNG is at `/tmp/claude-1000/-workspace/91f627b4-dcd2-4d42-8588-06dcf2e39371/scratchpad/qa.png`. Edge cases:
   - vx=-0.004 and vy=-0.005 give `vx 0.00` and `vy -0.01`. The vy value is stored just below -0.005, so it rounds to -0.01 and keeps its minus.
   - x=-0.0 gives `x 0.00`.
   - vx=-0.005 gives `vx -0.01`.
   - ±1e6 prints normally.
   - `overlay_text_bottom()` is still 52, unchanged by the format change.
4. **Assumptions:** The `z` option is untested in the browser runtime (reviewer finding 1). A headless desktop run on Python 3.12 can't check it. That check belongs to the Integration Engineer.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Confirm in a browser debug build (`debug=1`) that the overlay draws with no `ValueError`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core PASS · ui PASS (8 passed)
QA: pass
