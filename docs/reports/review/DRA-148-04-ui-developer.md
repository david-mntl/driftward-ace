Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of DRA-148-04 (the level-up banner view), requested by the `/implement` skill. Read against `docs/contracts/systems/level-up/view.md`, `rationale.md` and the task file `docs/contracts/DRA-148/tasks/DRA-148-04-ui-developer.md`.
2. **Delivered:** this report, `docs/reports/review/DRA-148-04-ui-developer.md`. Code reviewed: `game/ui/level_up_view.py` (read only; `ui/level_up_rules.py`, `ui/level_up_motion.py`, `tuning/level_up.json` read for context).
3. **Checks:** by reading only, nothing run. I also looked at the implementer's own PNGs `shots/zoom.png` and `shots/banner_052_glint.png` (scratchpad) to confirm the glint finding against the code. Timings, pixel counts and surface counts in the implementer's report are not reproduced by me; the code has no path that builds a surface, renders text or scales in a draw method, so those claims are consistent with it. Not verified: the "0 fuchsia" count (no fuchsia color in `tuning/level_up.json`, none named in code).
4. **Assumptions:** The contract's "the number's own pixels" is read as the digit's fill pixels, not its outline, as the Director's session pointed out. The outline is a dark `panel_body` color there to separate the digit from the field.
5. **Documentation differences:** None in the docs themselves. One contract break in the code, stated first: `view.md`, Presentation, "The number": the glint lights "only the number's own pixels". The code also lights the dark outline pixels (F1). No change to any document is proposed.
6. **Next:** Implementation fix by the UI Developer, Review fix mode, on F1 (must-fix) and F3 (should-fix). F2 is a note for the Director: a private name of `ui/hud.py` is imported; making it public is a rename in task 05's file.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-148-04-F1 | must-fix | game/ui/level_up_view.py:415 | fixed |
| DRA-148-04-F2 | note | game/ui/level_up_view.py:21 | not fixable |
| DRA-148-04-F3 | should-fix | game/ui/level_up_view.py:341 | fixed |

### DRA-148-04-F1
The glint frames light the outline as well as the digit. `_glint_frame` (line 415) takes `poses[-1]`, the full canvas of `_digit_image`, whose alpha covers the glyph and its 2 px dark outline (lines 358 to 368). It copies that alpha into `tint` (lines 439 to 441), keeps it through the stripe mask (442) and blits the tint over the frame (443 to 444). So every outline pixel inside the stripe is turned pale at `glint.strength`. The outline fills the narrow gaps of the "3", so the stripe shows as a pale slanted block spilling past the strokes (`shots/zoom.png`, digits 5 and 6; `banner_052_glint.png`). It reads as a rendering glitch, and the report line 14 ("lighting only the digit's own pixels") does not match the picture.
Rule: `view.md`, Presentation, "The number": the glint lights "only the number's own pixels". Checklist 1 and 10.
Change: build the tint from the digit's fill pixels only, so the stripe's alpha is the glyph's alpha, not the canvas's. For example keep the cropped glyph alpha (or the fill image) from `_digit_image` and make the glint mask from it, placed at the outline offset, so the outline pixels stay as they are. Still made once in `__init__`, still no per-frame work. Re-save the glint PNGs and check that the stripe stays inside the strokes.

### DRA-148-04-F2
`ui/hud.py` imports `Tiles` and the private `_ink_tiles` (line 21, used at 562); the contract's import list for this module names `HudView` and `LevelSlot`. The contract does ask for the HUD's sheen method, so the reuse is right; only the private name crossing modules is a smell. The implementer flagged it. Change: none here; the Director may later make it public or move it to a shared `ui` module (a rename in task 05's file).

### DRA-148-04-F3
The number's center is computed twice: `__init__` lines 110 to 114 (`_number_center`) and `_build_number` line 341 (`center_y`, a second copy of the same sum). Rule: no duplicated blocks (checklist 8); if `band.center_offset_y` or `number.center_offset_y` logic changes, the fall distance and the draw position drift apart.
Change: compute the center once and pass it to `_build_number`, or derive `drop_px` from `_number_center`.

## Checklist
1. Interface matches exactly: F2
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. Smells: F3
9. pass
10. Report claims match the files: F1

## For QA
- Glint at ages 44 to 60 on levels 2 to 8 (digits with counters or gaps: 3, 8, 6, 2): the stripe must light only the strokes, never the outline or the gaps.
- Hold at age 80 and ages 22 to 34: ring, streaks, LEVEL and pips draw behind the number and never over a drifter or the ship (stand-ins drawn after the banner).
- Glass edge ages 0 to 10 and 100 to 124: hairlines sit on one row when the glass is at height 0, no stray pixels at the walls.
- Pause on a banner age: the picture holds (the view keeps no state; the age is the only clock).
- Browser: the frame cost of the glass at full height (measured only headless by the implementer).

## Re-check 2026-11-06
1. **Task:** Re-check of the Review fix for DRA-148-04 (F1, F3), requested by the `/implement` skill.
2. **Delivered:** this section in `docs/reports/review/DRA-148-04-ui-developer.md`. Code read: `game/ui/level_up_view.py` lines 105 to 120, 327 to 457 (only the code the fix changed).
3. **Checks:** by reading only, nothing run. The implementer's fix check ("0 visible pixels changed outside the fill") is consistent with the code.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Round 2 fixes only the open must-fix and should-fix: none are open. The task goes to QA Engineer.
7. **Status:** done.

- DRA-148-04-F1: fixed. `_digit_image` (`game/ui/level_up_view.py:376`) now returns a second image, the glyph's alpha placed at the outline offset (fill only). `_glint_frame` (`:451`) builds the tint from that image, so the stripe's alpha is the fill's alpha and the outline cannot be lit. Still built once in `__init__`; same size as `poses[-1]`, the 1x number.
- DRA-148-04-F2: not fixable. The implementer's `Not fixable:` line names it: the private `_ink_tiles` lives in `ui/hud.py` (task 05's file), a Director decision. It was a note with no change asked.
- DRA-148-04-F3: fixed. `_build_number` (`:327`) takes `center_y`; `__init__` passes `self._number_center[1]` (`:117`); `drop_px` (`:350`) uses it. The second copy of the sum is gone.
