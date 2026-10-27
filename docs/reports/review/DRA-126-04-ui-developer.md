Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-126-04 (ui-developer: game-over message, name picker, grey choices), as passed on by the `/implement` skill. Task file: `docs/contracts/DRA-126/tasks/DRA-126-04-ui-developer.md`.
2. **Delivered:** `docs/reports/review/DRA-126-04-ui-developer.md` (this file). Reviewed: `game/ui/game_over.py`.
3. **Checks:** Read through, nothing run. Compared against `docs/contracts/systems/game-flow.md` (Interface, both `ui/game_over.py` blocks and the `ui/screen_look.py` block; Presentation, the GAME_OVER rows, the shared items and Game-over screen; Rules, Values; Rationale, "New fields and parameters have defaults"), `docs/contracts/systems/saves.md` Interface, `docs/contracts/DRA-126/impact.md`, scope report DRA-126 Values needed, `docs/reports/DRA-126-away-log.md` Decisions 4, `10-ui.md` game_over_message, `game/CONTEXT.md` and `game/ruff.toml`. Every constant, signature and default matches the contract. The layout math gives the DRA-125 tops when the picker heights are 0, and the six contract lines with the picker. Every value traces to a source. Result: 1 note, no changes asked.
4. **Assumptions:** The implementer's slot count `len(picker.slots)` stands in for `NICKNAME_LENGTH`. The two are the same by `saves.md` (NamePicker, `slots`), and values inside core are trusted (`game/CONTEXT.md`). Accepted, not a finding.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on `docs/reports/review/DRA-126-04-ui-developer.md`. Open findings: 0 must-fix, 0 should-fix, 1 note (no action).
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-126-04-F1 | note | game/ui/game_over.py:205 | no action |

### DRA-126-04-F1
`_Layout(box_size, box_left, box_top, *tops)` fills six named fields from a list by position. mypy can't check how many values the list holds, so a seventh height would fail only at run time. Rule: every value has a known type (`game/CONTEXT.md`, Types). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F1
9. pass
10. pass

## For QA
- Top-10 game over: picker shows, the cursor outline sits on slot 0, the hint shows, RETRY and MENU are grey with no `>`.
- Move the cursor to slot 9 and confirm: the outline and the hint go away, the slots keep the name, and no other line moves. RETRY turns white with `>`.
- Blank slots draw nothing. A picked `_` shows as a character above its underline, not as a blank slot.
- Off the list, or saves off: the DRA-125 box and lines, GAME OVER, RETRY and MENU white from the start.
- Turn a slot to the widest characters (`W`, `@`, `M`): each stays inside its cell and the 24 px slot row doesn't overlap the score line above.
