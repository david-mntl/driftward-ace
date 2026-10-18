Status: reviewed
Created by: implementation-reviewer

1. **Task:** review the points popup's view, task `docs/contracts/DRA-62/tasks/DRA-62-04-ui-developer.md`, built by the UI Developer. Report: `docs/reports/implementation/ui/DRA-62-04-ui-developer.md`.
2. **Delivered:** this file, `docs/reports/review/DRA-62-04-ui-developer.md`. Code read: `game/ui/popup_view.py`, plus `game/core/popup.py` (the type it draws), `game/ui/hud.py` (style reference) and `game/ruff.toml`.
3. **Checks:** by reading only, nothing run. Compared the code with `docs/contracts/systems/run.md` (Interface, `game/ui/popup_view.py`; Presentation, Points popup; the `run.popups` row), `drifters/04-coin.md`, `CLAUDE.md` and `docs/design/gdd/15-tech-constraints.md`.
   - Interface: `POPUP_COLOR`, `POPUP_FONT_SIZE`, `popup_text(points)`, `draw_points_popup(surface, popup)` match the contract in names, types, `Final` and values. The only helpers added are the two private cached ones.
   - Look, text, place and cache match the Presentation text. The font is `Font(None, 16)`, antialiased, with no outline or fade. The text is `f"+{points}"`. The center is `(round(popup.x), round(popup.y))`. The font is built once and the text is cached once per points value.
   - The acceptance command's expected image is the same blit the code makes, so the claimed `+50 +100 True` can be passed by this code. The popup's `y` at age 30 is 164 - 15 = 149, which is the task's center.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, with this report. The app's per-frame draw call and the popup layer are the Integration Engineer's work, so popups are not on screen until `game/app/frame.py` calls the view.
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
- Draw a `+100` popup at age 0 and at age 20: the text is 10 px higher at age 20 (0.5 px per tick) and not clipped.
- Draw the same popup twice: the second draw is pixel-identical to the first, and only two text surfaces exist after drawing 50 and 100.
- Collect a coin close to the top or right edge: the popup is clipped by the surface and nothing raises.
- After the app wires it (DRA-62 integration): the popup shows over the drifters and under the ship, and it vanishes at once after 60 ticks.
