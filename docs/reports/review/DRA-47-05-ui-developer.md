Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of `docs/reports/implementation/ui/DRA-47-05-ui-developer.md` (task `docs/contracts/DRA-47/tasks/DRA-47-05-ui-developer.md`, the architect's). Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-47-05-ui-developer.md`.
3. **Checks:** By reading only. I compared `game/ui/drifters/entry_warning.py` (all 131 lines) with `docs/contracts/systems/drifters.md`: the Interface for `game/ui/drifters/` (lines 649 to 662) and for `warning_copy` in `base.py` (line 369), the Presentation rows for `obj.warning_copy()` and `obj.width` (lines 705 and 707), and Entry warning (lines 735 to 740). I also checked `07-drifters.md` `entry_warning_size`, `drifters/03-chain-lightning.md` `entry_warning_icon` and `entry_warning_size`, `game/core/drifters/base.py:299` and `game/core/drifters/chain_lightning.py:307`. `_build_image` (lines 86 to 93) calls `warning_copy()` once, sizes R on `copy.width`, seeds the spikes with `drifter.uid`, and passes the copy and `drifter.warning_tilt_degrees()` to `_draw_copy`. `_draw_copy` (lines 104 and 107) calls `view(..., copy, center, ENTRY_WARNING_SCALE, 1.0)`. I traced the acceptance command by hand: an 80 px copy gives R 40 and a 60 px glow span (> 50). A 20 px meteorite gives R 10 and a span of at most 20, counting spikes. Both match the printed output in the report. I ran nothing.
4. **Assumptions:** The first parameter is named `drifter`, not the contract's `obj`, in `draw_entry_warning` and `drop_entry_warning`. That name dates from DRA-29, was noted the same way in the DRA-39-02 review, and lies outside this task's delta, so I did not flag it. The module-level `_IMAGES` cache is the contract's own design (Entry warning, Pre-rendered), not game state.
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
- Spawn a chain lightning of any variant: the warning is 141 px square (R 70), with three half-size cyan discs in a point-up triangle, whatever the variant or `invert`.
- Spawn small, medium and big meteorites and both satellites: the warnings look exactly as before DRA-47 (R 10, 14, 20 and 18; the angled satellite's copy is still turned 20 degrees).
- Two chain lightnings of different variants at once: each warning keeps its own spikes (seeded by uid), and the image is dropped when each one turns ACTIVE.
