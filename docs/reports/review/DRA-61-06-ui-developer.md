Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of `docs/reports/implementation/ui/DRA-61-06-ui-developer.md` (the SCORE line in `game/ui/hud.py`), asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-61-06-ui-developer.md` (this file).
3. **Checks:** Read `game/ui/hud.py` against `docs/contracts/systems/hud.md` v2 (Interface, Presentation, Rules, DRA-61 Impact and Rationale), task `DRA-61-06-ui-developer`, `game/ui/score_text.py`, `game/tests/ui/test_hud.py`, `game/CONTEXT.md`, `game/ruff.toml`, `10-ui.md` (rule 2, hud_score) and `15-tech-constraints.md` (rule 5). Ran nothing.
4. **Assumptions:** The `lru_cache` on `_score_surface` counts as a render cache like the existing `@cache` helpers, not module-level game state.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on `docs/reports/implementation/ui/DRA-61-06-ui-developer.md` and task `DRA-61-07-qa-engineer`. Open findings: 0 must-fix, 0 should-fix, 1 note (no action).
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-61-06-F1 | note | docs/reports/implementation/ui/DRA-61-06-ui-developer.md:9 | no action |

### DRA-61-06-F1
The task's Acceptance check asks for the screenshot "command, the output and the image path". The report describes the calls in prose and gives the output and path, but not a command QA can paste. Source: task DRA-61-06, Acceptance check. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. n/a
5. pass
6. pass
7. n/a
8. pass
9. pass
10. F1

## For QA
- Score crossing a group boundary (999 to 1 000, 999 999 to 1 000 000): the HUD text changes on that frame, not one late.
- Retry after Game Over: SCORE shows `SCORE 0` again (the one-slot cache must re-render for 0).
- Debug mode with F3 toggled: SCORE stays below the overlay's place and nothing is drawn on line 2.
- Same score over many frames: `_score_surface` returns the same surface (no per-frame render).
- Game Over box up: the HUD SCORE and the box's score line show the same text.
