Status: reviewed
Created by: implementation-reviewer

1. **Task:** review the UFO view and its registration (task `docs/contracts/DRA-104/tasks/DRA-104-03-ui-developer.md`, implementation report `docs/reports/implementation/ui/DRA-104-03-ui-developer.md`), from the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-104-03-ui-developer.md` (this file).
3. **Checks:** by reading only. I read `game/ui/drifters/ufo_view.py` and `game/ui/drifters/__init__.py` against drifters.md (Interface, `game/ui/drifters/`; Presentation, the UFO row, Brightness, UFO, Entry warning, Rules for every view; Rationale, the DRA-104 lines on size and `DOME_DRAW_MARGIN`), `ufo_hitbox` (`game/core/drifters/ufo.py:84`), `ui/shapes.py` (box and circle rounding), `ui/drifters/registry.py`, drifters/07-ufo.md (placeholder_look) and `game/CONTEXT.md`. I worked the task's five expected lines through `draw_shape`'s rounding: disc on columns 300 to 339, rows 295 to 304; dome center (320, 295), radius 9; the dimmed colors from `dim_color`. All five agree with the code. Nothing run.
4. **Assumptions:** The `drifter` versus `obj` parameter name is treated as a note with no change, as in the DRA-56-02 and DRA-86-06 reviews: `DrifterView` is a positional `Callable` and every view uses `drifter`.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no change asked. The `check.sh core` collection failure the report names is the one the drifters contract's DRA-104 Impact table assigns to DRA-104-04.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-104-03-F1 | note | game/ui/drifters/ufo_view.py:29 | no action |

### DRA-104-03-F1
The second parameter is `drifter`; the Interface names it `obj` (drifters.md, Interface, `game/ui/drifters/ufo_view.py`, line 1645). Every other view and `DrifterView` use `drifter`, and `registry.py:70` calls views positionally, so nothing breaks. Change: none.

## Checklist
1. Interface matches exactly: F1
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- A weaving UFO: dome and disc move together each frame, the disc drawn over the dome's lower half.
- Hit a UFO: during the re-hit cooldown both parts dim together, (128, 128, 139) and (68, 165, 83), and return to full color when the cooldown ends.
- Entry warning at (12, y) or (628, y): a small grey bar with green on top, untilted, inside the glow.
- Debug mode: the box and circle outlines sit exactly on the drawn disc and dome.
- A hitbox that is not a Box then a Circle raises `TypeError("render_ufo draws a box then a circle, disc then dome")`.
