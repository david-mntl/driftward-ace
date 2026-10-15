Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-29-05-ui-developer (object view registry, shared entry warning, placeholder meteorite), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-29-05-ui-developer.md. No test files saved (Verify saves none). Inline script kept outside the repo in the scratchpad (`qa05.py`).
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (env, lint, format, typecheck, core 35 passed, ui 11 passed).
   - Acceptance check, exact task text, run from `game/` with `PYTHONPATH=.`:
     ```
     ['meteorite'] (160.0, 10.0) (140, 140, 140) True 76
     True True True
     (140, 140, 140) 308 0
     ```
     Matches the task: warning at the top edge with a grey copy (76, near 80) on glow; all ink inside x 150..170 and rows 0..20; ACTIVE is a grey disc (308, near 314) with no glow.
   - Review For QA items, all correct:
     - Small, medium, big at x 0, 640, 320, -50 and 700 (centered on `warning_center()`): the ink box stays inside the rock's own width and on screen. Examples: small at x 0 gives box x 3..19, y 3..18. Big at x 640 gives x 605..638, y 5..37.
     - Different uids give different pixels. The same uid gives identical pixels, and three consecutive frames are identical.
     - Cache: 50 objects in WARNING leave 50 entries. After all 50 draw ACTIVE the cache holds 0 entries.
     - GONE draws nothing (surface unchanged, no cache entry).
     - With the view registry emptied, `render_object` raises `ValueError: no view registered for object type 'meteorite'` in WARNING, ACTIVE and GONE.
     - A second view for METEORITE raises `ValueError: view for object type 'meteorite' is already registered`.
   - Other edges, all correct:
     - `repr` of the object is unchanged by drawing.
     - Warning blits with alpha onto a non-black background (background pixel (0,0) stays (10,20,30), the copy pixel is grey).
     - ACTIVE draws at (-100,-100), (1000,1000) and (0,0) raise no error (clipped).
   - Review Findings 1 and 2: closed in the code (`drop_entry_warning` is in `objects.md:361`; the constants are `Final`). No `Fix` sections apply.
   - No automated test exists for the warning or the meteorite look, by design (DRA-29-09). The look is for the Integration Engineer to check by eye in the browser.
4. **Assumptions:** Edge expectations come from `objects.md` Presentation (side `2 * ceil(R) + 1`, nothing past R, a warning of `warning_ticks` frames) and the GDD guesses it cites. Review Round 1 Re-check records the Director's approval of `drop_entry_warning` (`objects.md:362`). I did not re-verify it.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Check the warning and the grey rock by eye in the browser (no automated test covers them).
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (35 passed) · ui PASS (11 passed)
QA: pass
