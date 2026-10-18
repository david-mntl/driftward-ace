Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-39-02-ui-developer.md` against task `docs/contracts/DRA-39/tasks/DRA-39-02-ui-developer.md`, the parts of `docs/contracts/systems/drifters.md` it names, the GDD and `CLAUDE.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-39-02-ui-developer.md`.
3. **Checks:** By reading only. I read the three delivered files: `game/ui/drifters/registry.py`, `entry_warning.py` and `meteorite_view.py`. I compared them with drifters.md: Interface (`game/ui/drifters/` block), Presentation (the `warning_tilt_degrees()` and `brightness()` rows, Brightness, Meteorite, Entry warning Copy and Pre-rendered, Rules for every view), and Rules, The base (Warning tilt, Re-hit cooldown). I also read `game/core/drifters/base.py` (`warning_tilt_degrees`, `brightness`), `docs/design/gdd/05-lives-and-damage.md` (rehit_dim 0.75, guess), `docs/design/gdd/drifters/02-satellite.md` (rule 1, placeholder_look), `game/CONTEXT.md` and `game/ruff.toml`. By hand: `dim_color((60, 110, 220), 0.75)` gives (45, 83, 165) and `dim_color((140, 140, 140), 0.75)` gives (105, 105, 105), the numbers the acceptance check expects. A tilt of -20 through `pygame.transform.rotate` turns the copy clockwise, so the test bar's right end is lower. That fits the expected `True`. A grep of `game/` for `DrifterView`, `dim_color` and `render_meteorite` finds no caller left with the old four-argument view. Nothing was run.
4. **Assumptions:** The first parameter is named `drifter`, not the contract's `obj`, in `render_drifter`, `draw_entry_warning` and `render_meteorite`. That name dates from DRA-29, is used positionally and is outside this task's DRA-39 delta, so I did not flag it.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no action. No must-fix or should-fix.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-39-02-F1 | note | game/ui/drifters/entry_warning.py:98 | no action |

### DRA-39-02-F1
`_draw_copy` works out the image center again from `get_width() // 2`. It types it as `tuple[float, float]` and calls `round` on ints at `:106`. `_build_image` already has the same `center` (`:86`). The result is correct, because the side is odd. Rule: keep functions short and code plain (`game/CONTEXT.md`, Good practice). Change: none.

## Checklist
1. pass
2. pass
3. n/a
4. pass
5. pass
6. pass
7. pass
8. F1
9. pass
10. pass

## For QA
- An active meteorite draws (140, 140, 140). With `rehit_ticks_left` > 0 it draws (105, 105, 105). It is back to (140, 140, 140) on the first frame drawn from a state with `rehit_ticks_left` 0.
- A warning drawn for a drifter whose `rehit_ticks_left` > 0 still draws its copy at full brightness (the copy always passes 1.0).
- With tilt 0, the warning image matches the DRA-29 pixels exactly. With a non-zero tilt, the glow and spikes match the tilt-0 image, and the turned copy's middle stays on the image's middle pixel.
- Two drifters with the same uid, type and variant but different tilts get separate cached images. `drop_entry_warning` still empties the cache once the drifter turns ACTIVE.
- `tests/ui/test_drifter_registry.py` is expected to fail from DRA-39-03 until DRA-39-04 adds the satellite view (drifters.md, Impact).
