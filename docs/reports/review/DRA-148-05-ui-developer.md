Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-148-05 (UI Developer): the HUD level pop, `LevelSlot`, the optional look and banner arguments, the shown level and `level_slot`, in `game/ui/hud.py`. Asked by the `/implement` skill.
2. **Delivered:** this review, `docs/reports/review/DRA-148-05-ui-developer.md`. Reviewed by reading: `game/ui/hud.py`, with `game/ui/level_up_rules.py`, `game/ui/level_up_motion.py`, `game/core/level_up.py`, `docs/contracts/systems/level-up/view.md`, `docs/contracts/systems/hud.md`, the level-up schema and `tools/art/hud_panel.py` (box corners).
3. **Checks:** read only, nothing run. The Interface (`LevelSlot`, `HudView.__init__`, `draw`, `level_slot`) matches the contract signature for signature. The cut corners (top-right and bottom-left) match the art tool's `_box` at `tools/art/hud_panel.py:279-282`. The implementer's check claims (pixel equality, surface count, lint, typecheck, ui tests) are ones the code can pass: no per-frame render, surface or scale call is reachable in the pop path. I could not confirm them without running.
4. **Assumptions:** The implementer's pop-frame rounding and the arrival size `round(size * start_scale)` are taken as the contract's silence filled in sensibly; the flight (task -06) must use the same rounding.
5. **Documentation differences:** None that break the contract, the pillars or a locked decision. One small gap is in F1 (a note).
6. **Next:** QA Engineer, on this report. No finding asks for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-148-05-F1 | note | game/ui/hud.py:23 | no action |
| DRA-148-05-F2 | note | game/ui/hud.py:45 | no action |
| DRA-148-05-F3 | note | game/ui/hud.py:299-308 | no action |

### DRA-148-05-F1
`hud.py` imports `ui.level_up_motion` (`fade_share`, `pop_scale`). The contract's import line for `hud.py` lists only `core.level_up`, `core.levels` and `ui.level_up_rules` (view.md, Interface). The import is the right choice: it keeps every curve out of `hud.py`, and there is no import cycle. The contract's comment is the one that is short. Change: none. The Architect may add the module to that line.

### DRA-148-05-F2
`INK_TILE = 16` is a literal. It is a build-time cell size, not a game value, and the report says so. The sheen reads its row height from `hud.json`; this one does not. Change: none.

### DRA-148-05-F3
`level_slot` is documented "pure", but with no look it fills the number cache on a first call (`hud.py:303`). Nothing visible changes, and with a look every number is built in `__init__`, so the call touches nothing. The report's Decisions state it. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass (F2 is an implementation constant, no action)
7. pass
8. pass
9. pass
10. pass

## For QA
- Run a level rise and watch the level box: the old level until the arrival tick, then the new number at about 1.5x, undershooting, settling to normal. The new climb bar and the box outline flash and fade.
- Pause during the pop: the pop must freeze (it reads the banner's age, not the view clock) and resume where it stopped.
- Build the HUD with no look, and with a look but no banner: it must look exactly like the old HUD.
- Check the box outline's flash sits on the baked outline, with both cut corners lining up.
- Frame rate in the browser while the pop plays (about 16 small blits plus a few fills): the project's open frame-rate problem.
