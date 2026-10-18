Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of `docs/reports/implementation/ui/DRA-47-06-ui-developer.md` (task `docs/contracts/DRA-47/tasks/DRA-47-06-ui-developer.md`, written by the Architect). Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-47-06-ui-developer.md`.
3. **Checks:** By reading only. I compared `game/ui/drifters/chain_lightning_view.py` (all 110 lines) and `game/ui/drifters/__init__.py` with `docs/contracts/systems/drifters.md`: the Interface for `chain_lightning.py` (lines 534 to 615) and `game/ui/drifters/` (lines 631 to 695), the Presentation rows for the chain lightning (lines 709 to 711), Brightness (line 717), Chain lightning (lines 723 to 728) and Rules for every view (lines 742 to 745). I checked the colors, the 45° first ray and the sizes against `drifters/03-chain-lightning.md` (node_size, arc_width, charge_rays, ray_length, placeholder_look), and the core methods the view reads at `game/core/drifters/chain_lightning.py:255` and `:273`. I traced the acceptance command by hand. Nodes at (256, 100) and (384, 100). Tick 0 gives 1 ray at 45°, from about (260.2, 95.8) to (264.5, 91.5), inside the up-right box. Tick 90 gives `1 + 90 × 4 // 120` = 4 rays. Tick 120 fires a 6 px band, so (320, 93) stays black. `rehit_ticks_left` 10 gives 0.75 brightness. All four lines match the printed output. I ran nothing.
4. **Assumptions:** The `drifter` parameter name goes back to DRA-29. The DRA-39-04 review called the same thing a note, so I log it as a note too (F1), not as a contract break. The module-level `log` that is never called follows `meteorite_view.py` and `satellite_view.py`. I did not flag it.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Two notes, no action. No open must-fix or should-fix.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-47-06-F1 | note | game/ui/drifters/chain_lightning_view.py:43 | no action |
| DRA-47-06-F2 | note | game/ui/drifters/chain_lightning_view.py:36 | no action |

### DRA-47-06-F1
The second parameter is `drifter`. The Interface names it `obj` (drifters.md, Interface, `game/ui/drifters/`, line 689). Every other view and `DrifterView` use `drifter`, the registry only calls views positionally, and the report states it under Assumptions. Change: none.

### DRA-47-06-F2
`FULL_TURN_DEGREES` is a public module constant that the Interface does not list (drifters.md, lines 682 to 686). It stands in for the contract's literal 360, a unit fact rather than a game value, and the report states it under Assumptions. Change: none.

## Checklist
1. Interface matches exactly: F1, F2
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
- Watch one full cycle of each layout: no band while charging, rays grow from 1 to 4 per node (45°, 135°, 225°, 315°), then the band shows with no rays.
- Fire a chain with one node off screen: only arcs whose two nodes are on screen draw. The band and the hitbox must match (rule 9).
- Get hit by a firing chain: band, nodes and any rays dim to 0.75 together and come back to full colors when the cooldown ends.
- During the warning, the copy shows only three half-size cyan discs: no band and no rays.
- Toggle the debug overlay on a firing chain: each band covers its line outline exactly.
