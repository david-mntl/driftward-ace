Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-104-03-ui-developer (the UFO view `render_ufo` and its registration), started by /implement. Review status was `reviewed` (one note, no change asked).
2. **Delivered:** docs/reports/qa/DRA-104-03-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui pass (ui: 46 passed, including `test_drifter_registry.py`). `core` fails at collection, `tests/core/test_collision.py:1753 KeyError: 'hitbox'`: `load_variant_cases` reads `raw["hitbox"]` from `game/tuning/drifters/ufo.json`. The drifters contract's DRA-104 Impact table assigns that to QA task DRA-104-04. Nothing in `game/ui/` causes it.
   - Acceptance check: I ran the task's command exactly (from `game/`, SDL dummy). The five lines match the task line for line: `(170, 170, 185) (170, 170, 185) (170, 170, 185)`, `(90, 220, 110) (90, 220, 110)`, `(0, 0, 0) (0, 0, 0) (0, 0, 0) (0, 0, 0)`, `(128, 128, 139) (68, 165, 83)`, `(170, 170, 185) True True`.
   - Look at full size: the disc is columns 300 to 339 and rows 295 to 304 (400 px, a full 40 x 10); the dome shows on rows 286 to 294 (the lower half is under the disc). Moving to y 250 moves both (disc rows 245 to 254, dome 236 to 244).
   - Dimming: through `render_drifter`, `rehit_ticks_left` 180 and 1 draw (128, 128, 139) and (68, 165, 83); at 0 the full colors return. Brightness 0 gives black, 0.5 gives (85, 85, 93) and (45, 110, 55).
   - Entry warning (real WARNING phase through `render_drifter`): center (12, 300) and, with `invert`, (628, 300). The disc is a 14 x 4 bar (rows 298 to 301) with a green dome of 12 px on top (rows 295 to 297). Untilted, inside the glow side. Same shape on both sides.
   - Edges: a UFO at x 0 and x 640 draws only the part on the surface (no error); at x -20, 660, -100 and 700 it draws nothing; GONE draws nothing; scale 0 draws nothing; scale 2 gives a 80 x 20 disc.
   - Hitbox check: a circle only, a box only, circle then box, three shapes and an empty hitbox each raise `TypeError("render_ufo draws a box then a circle, disc then dome")`.
   - Debug outlines: the 1 px outlines of the UFO's hitbox (142 px) all fall on filled pixels of the drawn UFO.
   - Purity: two draws of one state give identical bytes; `repr(ufo)` is the same before and after.
   - Edge cases that behave correctly are not listed further. No bug found.
4. **Assumptions:** The task says `core` may fail until the UFO's tuning file and the QA tasks exist, so I took the one `core` failure as expected, not as a bug. The warning bar is 14 x 4 px on screen, not 14 x 3.5, because `draw_shape` rounds a box height to whole pixels (`round(3.5)` is 4); the task's own fifth line (fewer than 80 grey pixels) holds.
5. **Documentation differences:** None.
6. **Next:** No bug is open for DRA-104-03. The verdict is `blocked` only because `check.sh` does not end `QA: pass`, and the one failure comes from a later queued task, DRA-104-04 (the collision test's UFO case). The /implement skill can continue and re-check this task's harness after DRA-104-04. The Integration Engineer takes it once `check.sh` ends `QA: pass`. Open from DRA-104-01: its B1 (`docs/reports/qa/DRA-104-01-gameplay-implementer.md`), Gameplay Implementer.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (collection: `tests/core/test_collision.py:1753 KeyError: 'hitbox'`, expected until DRA-104-04) · ui PASS (46 passed)
QA: fail (core)

## Round 2 2026-10-22

1. **Task:** Re-test of DRA-104-03-ui-developer after DRA-104-04 and DRA-104-06 landed. Round 1 was `blocked` only because `check.sh` failed on the UFO collision case. Started by /implement.
2. **Delivered:** docs/reports/qa/DRA-104-03-ui-developer.md (this round, line 1 set to `Verdict: pass`).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`: core 3132 passed, ui 46 passed (including `test_drifter_registry.py`). The round 1 failure (`tests/core/test_collision.py:1753 KeyError: 'hitbox'`) is gone. `game/ui/` is unchanged since round 1 (`ufo_view.py` and `ui/drifters/__init__.py` as before), so the round 1 acceptance check and edge cases still stand. `render_ufo` imports and loads headless. No new bug.
4. **Assumptions:** The DRA-104-01 B1 is fixed and re-tested in its own report, so I did not count it here.
5. **Documentation differences:** None.
6. **Next:** No bug is open for DRA-104-03. Integration Engineer.
7. **Status:** done.

## Bugs
None. Round 1 had none.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3132 passed) · ui PASS (46 passed)
QA: pass
