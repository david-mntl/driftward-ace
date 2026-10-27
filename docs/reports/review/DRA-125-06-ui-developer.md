Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `game/ui/leaderboard.py` (DRA-125-06, UI Developer) against `docs/contracts/systems/game-flow.md` (Interface: `ui/leaderboard.py` and `ui/screen_look.py` blocks; Presentation: the page rows, the shared items, Leaderboard page, Instructions page Footer; Rationale: "Layout from font metrics"). Passed in by `/implement`.
2. **Delivered:** `docs/reports/review/DRA-125-06-ui-developer.md` (this file).
3. **Checks:** Read the implementation report, the task file, the contract sections the task names, `game/CONTEXT.md` (logger rule), `game/ruff.toml`, `docs/contracts/DRA-125/impact.md`, scope report DRA-125 (Values needed, lines 92-93), `game/ui/leaderboard.py`, and for comparison `game/ui/instructions.py` and `game/ui/screen_look.py`. Interface: both constants and `draw_leaderboard(surface) -> None` match exactly. Texts and sizes: "LEADERBOARD" at 32 px, "No scores yet." at 16 px, footer at 16 px, all via `ui.screen_look`, matching scope report lines 92-93. Footer top `height - 2 * body_line` is the same expression as `instructions.py:58`. Block height title line + blank body line + body line matches Presentation (Leaderboard page; Lines and blank lines), and ends at the last line's linesize, the same way the instructions page does. Nothing run.
4. **Assumptions:** The stdlib imports (`logging`, `functools`, `typing`) are within "Imports: pygame, ui.screen_look", as in the sibling views. The unused `log` follows `game/CONTEXT.md` line 31.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on `docs/contracts/DRA-125/tasks/DRA-125-06-ui-developer.md`. One note (F1) on duplicated private helpers. It asks for no change in this task.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-125-06-F1 | note | game/ui/leaderboard.py:50 | no action |

### DRA-125-06-F1
`_blit_centered` (line 50) and `_render` (line 56) are copies of `game/ui/instructions.py:93` and `:100` (and the menu has the same pair). That is a duplicated block (checklist item 8). But the contract limits this module's imports to pygame and `ui.screen_look`, and the `screen_look` Interface names no shared helper. So the copy is the contract-correct choice here. The implementer flags it under Next. A shared helper would be an Architect call for UI-03/UI-04. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. Smells: F1
9. pass
10. pass

## For QA
- Draw `draw_leaderboard` and `draw_instructions` on 640 x 480: the footer ink rows and columns must be identical.
- Draw twice on fresh surfaces: the bytes must be identical, and the second draw renders no new text (cache hits only).
- Draw on a non-640 x 480 surface (e.g. 800 x 600): everything stays centered on `width // 2`, and the block stays above the footer.
- Confirm `game/ui/leaderboard.py` imports nothing from `core` or `app`.
