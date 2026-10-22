Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-86-06 (floating island view and its registration), implemented by the UI Developer, against `docs/contracts/systems/drifters.md`. Requested by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-86-06-ui-developer.md` (this file). Reviewed: `game/ui/drifters/floating_island_view.py`, `game/ui/drifters/__init__.py`.
3. **Checks:** Read against the task file, the contract (Interface `game/ui/drifters/`, Presentation Floating island and Polygon shape, Rules Floating island Drawn parts, Impact, Rationale), `drifters/05-floating-islands.md` (hitbox, placeholder_look, rule 10), `game/CONTEXT.md` and `game/ruff.toml`. Traced the polygon inset by hand for the triangle: shoelace sum 38400 (positive), so the left normal of each edge points inside; reversed order (invert) flips the sign. Checked the acceptance output in the implementation report against the task's expected values: all six lines match. Nothing run.
4. **Assumptions:** The view parameter name `drifter` (contract: `obj`) is a wording difference, because `DrifterView` is a positional `Callable` and `registry.py:70` and `entry_warning.py:100,103` call views positionally. Logged as a note.
5. **Documentation differences:** Pending Director approval. The contract's Interface, `game/ui/drifters/` (`docs/contracts/systems/drifters.md:1167`, `:1228`-`:1304`) names the view's second parameter `obj`. All six views and the `registry.py` docstring name it `drifter`. Proposed change: the Architect renames `obj` to `drifter` in those view signatures and the `DrifterView` comment. Behavior is the same either way. This review does not depend on it.
6. **Next:** QA Engineer, with this report and `docs/reports/implementation/ui/DRA-86-06-ui-developer.md`. Open findings: 0 must-fix, 0 should-fix, 1 note (no action).
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-86-06-F1 | note | game/ui/drifters/floating_island_view.py:43 | no action |

### DRA-86-06-F1
The parameter is named `drifter`, but the contract's Interface names it `obj` (`docs/contracts/systems/drifters.md:1303`). Every other view does the same and views are only called positionally, so nothing breaks. Raised above under Documentation differences. Change: none.

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
- Draw every variant, and the L, T and triangle inverted: every pixel stays inside the footprint and the debug outline sits on the drawn edge.
- The L's and the T's joint: no dark line across the seam where the two boxes overlap.
- Triangle and inverted triangle: the ship stops on the drawn slope, not short of it or inside it.
- Over a long run with many islands, `_IMAGES` holds at most one image per variant and invert, and no image is rebuilt per frame.
- An island partly above the top edge or below the floor is clipped cleanly, with no error.
