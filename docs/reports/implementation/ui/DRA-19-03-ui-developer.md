Status: ready-for-review
Created by: ui-developer

1. **Task:** Fix the `HUD_FONT_SIZE` docstring in `game/ui/hud.py` (DRA-19-03, from the Architect).
2. **Delivered:** `game/ui/hud.py` (one docstring, no other line).
3. **Checks:** `grep -n -A2 "^HUD_FONT_SIZE" game/ui/hud.py` gives:
   ```
   22:HUD_FONT_SIZE: int = 16
   23-"""Readout text size, default font, px. Scope report DRA-13, temporary stand-in (readout text),
   24-not in the GDD (UI-01 is TBD)."""
   ```
   `game/tests/check.sh lint`: PASS lint, PASS format. Docstring-only change, so the draw run and core-state checks do not apply.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-19/tasks/DRA-19-03-ui-developer.md`.
7. **Status:** done.

## Decisions
- Wording copies the `HUD_COLOR` docstring pattern; unit, source and "UI-01 is TBD" kept. Other `HUD_*` docstrings untouched (layout values).
