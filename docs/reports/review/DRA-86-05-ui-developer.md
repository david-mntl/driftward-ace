Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-86-05 (the `Polygon` shape in `ui.shapes.draw_shape`), from `docs/reports/implementation/ui/DRA-86-05-ui-developer.md`, asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-86-05-ui-developer.md`.
3. **Checks:** Read `game/ui/shapes.py` against `docs/contracts/systems/drifters.md` (Interface `game/core/collision.py` `Polygon`, Interface `game/ui/shapes.py`, Presentation: Polygon shape and Rules for every view, Impact DRA-86 table), the task file, `game/CONTEXT.md`, `game/ruff.toml` and `docs/design/gdd/drifters/05-floating-islands.md` rule 10. Worked the acceptance check by hand from the code: row 240 gives `[160]`, row 355 160 to 467, row 359 ends at 478, row 360 is outside the row range; the square gives 100 pixels from (100, 100) to (109, 109); the outline hits (160, 300) and leaves (300, 330) empty. All match the task's expected output. The check.sh failures the report lists all sit in rows of the Impact table (`test_collision.py`, `test_wave_files.py`, `test_drifter_registry.py`). Ran nothing.
4. **Assumptions:** The `logging` import and `log` line are not new to this task and are required by `game/CONTEXT.md`, Logging; I read them as allowed beside the contract's "Imports: pygame, math, core.collision".
5. **Documentation differences:** None.
6. **Next:** QA Engineer. No open findings.
7. **Status:** done.

## Findings
None.

## Checklist
1. pass
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
- Draw the inverted triangle island: row 359 has one pixel at (160, 359), row 244 runs 160 to 467 (drifters.md, Presentation, triangle example).
- Turn on the debug overlay with an island on the field: polygon outlines draw and no `TypeError` is raised.
- A polygon partly off the surface (negative columns or rows past 480) draws clipped with no error.
- A polygon with non-whole corners (e.g. a center at x.5) fills by the pixel-center rule with no gaps or empty rows inside.
- Fill the same polygon twice: identical bytes, and its `points` unchanged.
