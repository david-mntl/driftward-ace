Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-148-06 (`LevelUpView.draw_flight` and the flight's pre-rendered sizes), asked by the `/implement` skill. Implementation report: `docs/reports/implementation/ui/DRA-148-06-ui-developer.md`.
2. **Delivered:** this report, `docs/reports/review/DRA-148-06-ui-developer.md`. Code read: `game/ui/level_up_view.py` (and `game/ui/level_up_motion.py`, `game/ui/level_up_rules.py` for the calls it makes).
3. **Checks:** by reading only, nothing run. Compared with `docs/contracts/DRA-148/tasks/DRA-148-06-ui-developer.md`, `docs/contracts/systems/level-up/view.md` (Interface, Presentation: The flight, Cost, What the views never do), `rationale.md` ("The flight ends on the pop's first size"), `docs/contracts/schemas/level-up.schema.json` (`fly`, `pop`). The implementer's check script lives outside the repo and was not run; its claims are consistent with the code.
4. **Assumptions:** none beyond the task's own reading list.
5. **Documentation differences:** None. No contract or locked-decision break found. One point to note (F2): the contract says both "ends on the arrival tick" and "draws up to, not including, `arrival_ticks`"; the code reads them as "the last drawn age is the end".
6. **Next:** Gameplay-side: none. The UI Developer, Review fix mode, answers F1 (should-fix). F2 and F3 ask for no change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-148-06-F1 | should-fix | game/ui/level_up_view.py:128 | fixed |
| DRA-148-06-F2 | note | game/ui/level_up_view.py:187 | no action |
| DRA-148-06-F3 | note | game/ui/level_up_view.py:433 | no action |

### DRA-148-06-F1
`self._hud` (line 128) and `self._field_origin` (line 129) are stored and never read again. The flight's start is kept as `_flight_start` (line 140) and its end comes from `_Flight.end`. The `__init__` docstring (lines 124 to 125) says both are "kept for the flight", which is no longer true. Dead state, and a view holding a reference to the HUD it never uses after startup.
Rule: no dead code (checklist 8; ui-developer standards).
Change: drop the two attributes and fix the docstring sentence; the parameters stay, the Interface is unchanged.

### DRA-148-06-F2
`fly_share(age, fly, banner.arrival_ticks - 1)` ends the ramp on the last drawn age. The contract's `fly_share` comment says "eased to 1 at arrival_ticks", yet `draw_flight` draws only below `arrival_ticks`, so the literal call would stop 1.9 px short of the slot, past the task's 1 px check. The implementer's choice satisfies the acceptance check and is stated in Decisions and Assumptions. It reads the two contract lines in the only way both can hold. `Change: none`. The Architect may want to word it in the contract.

### DRA-148-06-F3
The last flight image is the whole number, outline included, mixed flat to the tier color, with the digit's ink 23 x 33 inside a 23 x 51 image. The contract says the HUD's first pop frame "is the same image where it lands", and the HUD's pop frame 0 is flash white (task 05's design). So size and center match, but the hand-off may show a change of color and glyph shape on the arrival tick. The implementer states this in Assumptions. `Change: none`; QA should look at it.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. Smells: F1
9. pass
10. pass

## For QA
- Level up with the HUD visible: watch the number leave the field at `fly.start`, bow up along the arc, and land in the level box. Check for a jump in position, size or color on the arrival tick when the HUD pop starts (F3).
- Pause during the flight: the flight and the banner hold still and the flight is dimmed with the rest.
- Level up at every level (2 to 8): the number lands on that level's slot.
- Frame time over the banner, flight included, in the browser build: `draw_flight` should only blit.
- With a banner of None, before `fly.start` or from the arrival tick: nothing is drawn on the window.

## Re-check 2026-11-06

1. **Task:** Re-check DRA-148-06 after the implementer's Review fix, asked by the `/implement` skill.
2. **Delivered:** this file, `docs/reports/review/DRA-148-06-ui-developer.md` (line 1, findings table, this section).
3. **Checks:** by reading only, nothing run. Read `game/ui/level_up_view.py` lines 100 to 149 (`__init__`) and grepped the file for `_hud` and `_field_origin`: no hits. Read the `## Review fix` section of the implementation report. A later one-line QA bug fix to `drop_px` rounding (task 04, B1, near line 395) is outside this re-check and was not read.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Round 2 fixes only open must-fix and should-fix findings; none are open. The task goes to the QA Engineer.
7. **Status:** done.

- DRA-148-06-F1: fixed. `game/ui/level_up_view.py:120-149`: the `_hud` and `_field_origin` attributes are gone, `hud` and `field_origin` are used only in `__init__` to build `_flight_start` and `_flights`, and the docstring (lines 123-125) now says so. The Interface is unchanged.
- F2, F3: unchanged, no action.
