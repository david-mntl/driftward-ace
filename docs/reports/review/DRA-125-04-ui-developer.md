Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-125-04 (`game/ui/screen_look.py`, `game/ui/menu.py`) against `docs/contracts/systems/game-flow.md`, asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-125-04-ui-developer.md` (this file).
3. **Checks:** Read the implementation report, the task file, the contract parts the task names (Interface for `screen_look`, `menu` and `MenuItem`; Presentation shared items and Menu; the three Rationale items), scope report DRA-125 Values needed, `10-ui.md` menu_screen, `02-game-flow.md` menu_items, `15-tech-constraints.md` rule 5, `game/CONTEXT.md`, `game/ruff.toml`, and both delivered files in full. Interface: 6 of 6 `screen_look` names and 5 of 5 `menu` names match, with the same types. Every literal traces to scope report DRA-125 (or DRA-23 for the box color). Nothing was run.
4. **Assumptions:** The contract's Menu item "One blank title line (one title line's height)" overrides the shared "a blank line is one body line's height" for the menu, so `2 * title_line` in `menu.py:58` and `menu.py:69` is correct. `Font.size(" ")` measures text but does not render it, so the Cache rule ("never a render per frame") still holds.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. Two notes, both no action. F1 is for the Architect when DRA-125-08 lands.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-125-04-F1 | note | game/ui/menu.py:78 | no action |
| DRA-125-04-F2 | note | game/ui/menu.py:81 | no action |

### DRA-125-04-F1
The marker placement (`_blit_marker`) is private to `menu.py`. DRA-125-08's game-over choices need the same rule (contract, Presentation, Selection marker: "Shared by the menu and the game-over screen"), so a second copy is likely. The implementer flagged this in Assumptions. A shared helper would be an Interface change, which the Architect owns. Change: none.

### DRA-125-04-F2
`_blit_marker` calls `screen_font(...).size(" ")` and re-centers the cached label rect on every draw. This is a metric call, not a render, so it is within the contract's Cache rule (`15-tech-constraints.md` rule 5). Change: none.

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
- Draw the menu with each `MenuItem`. Only the selected label has a `>`, and it sits one space left of the label, with the same top.
- Switch the selection. The labels must not move, only the marker.
- Draw on a surface that is not 640 x 480. The block must re-center both ways.
- Call `draw_menu` many times. After the first draw, no new font or render should be built (cache hits only).
- The core test failures listed in the implementation report (Checks, `core`) that are not named one by one in `impact.md` must fail only for the DRA-125-01 reason.
