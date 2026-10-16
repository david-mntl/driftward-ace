Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-39-04-ui-developer.md` against task `docs/contracts/DRA-39/tasks/DRA-39-04-ui-developer.md`, the parts of `docs/contracts/systems/drifters.md` it names, the GDD and `CLAUDE.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-39-04-ui-developer.md`.
3. **Checks:** By reading only. I read the two delivered files, `game/ui/drifters/satellite_view.py` and `game/ui/drifters/__init__.py`. I compared them with drifters.md: Interface (`game/ui/drifters/` block, `satellite_view.py` and `__init__.py`), Presentation (the `obj.hitbox` row, Satellite, Brightness, Entry warning Copy and Place, Rules for every view) and Rules, Satellite (Variants, Warning). I also read `docs/design/gdd/drifters/02-satellite.md` (placeholder_look, size, hitbox, rule 8), `game/ui/drifters/registry.py`, `game/ui/drifters/meteorite_view.py`, `game/ui/shapes.py`, `game/core/drifters/satellite.py` (`warning_tilt_degrees`), `game/tuning/drifters/satellite.json` (body box first), `game/CONTEXT.md` and `game/ruff.toml`. By hand, for the acceptance check: at (100, 50) the bar fills x 82 to 117, y 47 to 52, and the body x 94 to 105, y 44 to 55. That gives white, blue, white, black at the four pixels. At 0.75, `dim_color` gives (180, 180, 180) and (45, 83, 165). The inverted angled copy turns +20° (counterclockwise), so its left end is lower, and the bar spans about 613 to 631 around x 622. Both lines read `True`. At scale 1.0, `center + box.cx * scale` equals `place_hitbox`'s `x + cx`, so the look sits on the debug outlines. Nothing was run.
4. **Assumptions:** The view's second parameter is `drifter`, not the contract's `obj`. That is the convention `render_meteorite` and `render_drifter` have used since DRA-29, and views are only called positionally through `DrifterView`. So I logged it as a note, not a contract break (F1). The DRA-39-02 review made the same call.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no action. No must-fix or should-fix. The debug-mode check in the task waits on the Integration Engineer's DRA-39 wiring (`docs/contracts/systems/app.md`).
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-39-04-F1 | note | game/ui/drifters/satellite_view.py:29 | no action |

### DRA-39-04-F1
`render_satellite` names its second parameter `drifter`. The Interface names it `obj` (drifters.md, Interface, `game/ui/drifters/`). It matches `render_meteorite` and is only called positionally, so it changes no behavior. Change: none.

## Checklist
1. F1
2. pass
3. n/a
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- An active flat satellite at (100, 50) draws white at (100, 50) and (100, 54), blue at (115, 50) and black at (115, 54). With `rehit_ticks_left` > 0 the same pixels read (180, 180, 180) and (45, 83, 165).
- Angled satellite warning: without `invert` the copy's right end is lower, at x 18. With `invert` the left end is lower, at x 622. The flat one's copy stays upright: an 18 × 3 bar with a 6 × 6 body.
- A hitbox that is not exactly two boxes (one box, or a circle) raises `TypeError` from the view.
- In debug mode, after integration: the full-size look sits exactly on the hitbox outlines while the satellite crosses.
- `tests/ui/test_drifter_registry.py` should now pass: satellite has a tuning file, a class and a view.
