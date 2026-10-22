Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/ui/DRA-76-06-ui-developer.md` against task `docs/contracts/DRA-76/tasks/DRA-76-06-ui-developer.md` and contract `docs/contracts/systems/debug-overlay.md` v4 (asked by the `/implement` skill).
2. **Delivered:** `docs/reports/review/DRA-76-06-ui-developer.md` (this file). Code reviewed: `game/ui/debug_overlay.py`.
3. **Checks:** Read only, nothing run. Compared the file with the contract's Interface, Presentation and Rules, with `10-ui.md` (debug_overlay_layout) and with `Run.level` (`game/core/run.py:120`) and `WaveRun.current_wave_id` (`game/core/waves.py:163`). Interface matches: `OVERLAY_TEXT_LINES = 6` (line 38), `draw_debug_wave_lines(surface, run) -> None` (line 60), `overlay_text_bottom()` uses `(OVERLAY_TEXT_LINES - 1) * linesize + max(linesize, font.get_height())` (line 80). Lines 5 and 6 sit at index 4 and 5 (`FIRST_WAVE_LINE`, lines 44, 67-68), the same x and spacing as lines 1 to 4 through the shared `_draw_text_line` (line 164). `wave none`, `wave rest` and `wave <id>` come only from `run.waves` being None and `current_wave_id` being None (lines 156-161). The level comes from `run.level`. The module docstring names the new function.
4. **Assumptions:** The unused-looking `log` at line 24 is the same as every other `game/ui` module (project convention), not a finding. I did not run the acceptance command; its claimed output is one the code can produce.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. The Integration Engineer must still call `draw_debug_wave_lines(surface, run)` right after `draw_debug_overlay` in `game/app/frame.py` (`systems/app.md`); until then lines 5 and 6 are not drawn and the HUD sits two line-heights lower in debug mode.
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
- Debug mode with no waves (test spawn list): line 5 reads `wave none`, line 6 reads `level 1`.
- A wave plays, then a rest gap starts: line 5 changes from `wave <id>` to `wave rest`, and the level follows `run.level` at each level change.
- Long wave id: the text is never cut, and the HUD still sits below `overlay_text_bottom()`.
- Lines 5 and 6 are visible only once `frame.py` calls `draw_debug_wave_lines`; before that the HUD sits two empty lines lower.
- Lines 1 to 4 and the hitbox outlines are unchanged: `tests/ui/test_hud.py` must pass untouched.
