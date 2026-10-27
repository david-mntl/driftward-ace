Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-125-05, the stand-in instructions page view `draw_instructions` (UI Developer), against `docs/contracts/systems/game-flow.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-125-05-ui-developer.md` (this file).
3. **Checks:** Read `game/ui/instructions.py` (103 lines) against the contract's Interface (`ui/instructions.py`, `ui/screen_look.py` blocks), Presentation (shared items, Instructions page) and Rationale ("Layout from font metrics", "One outline square for every icon"); the scope report DRA-125, Values needed (lines 83 to 92); `10-ui.md` instructions_page; `game/ruff.toml`; `game/ui/screen_look.py` and `game/ui/menu.py` for comparison; `impact.md` for the expected failures. The four public names and the signature match the Interface. The title, the six (title, line) pairs, their order and wording, 16 px icon and the footer text match the scope report. The block height (title line, 6 blank body lines, 6 heading rows plus 6 lines) and footer top (`height - 2 * body_line`) follow Presentation; the measured rows in the implementation report agree with that arithmetic (heading tops 132, 172, ... 24 + 16 px apart, last line bottom 360, footer at 456). Nothing run.
4. **Assumptions:** The unused module `log` follows the convention every `game/ui/` module keeps, so it is not counted as dead code.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: one note, no change asked.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-125-05-F1 | note | game/ui/instructions.py:93 | no action |

### DRA-125-05-F1
`_blit_centered` and `_render` (lines 93 to 102) are word for word the same as `game/ui/menu.py:72-89`, and the leaderboard page will likely add a third copy. Smell: duplicated blocks (reviewer checklist 8). A shared helper would be an addition to the `ui/screen_look.py` Interface, which only the Architect can make, so the implementer was right to keep them private. Change: none. The Director may ask the Architect to add a shared text helper to `screen_look` with UI-04.

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
- Draw the page on a surface other than 640 x 480 (for example 800 x 600): every row stays centered and the footer's top sits two body lines above the bottom.
- Draw twice and compare: the picture is the same and no text is rendered again (`_render` cache).
- Check the six icons are the same 16 x 16, 1-px outline, each one space left of its title and vertically centered with it.
- Confirm `draw_instructions` never fills the background: draw on a non-black surface and see that surface's color stays around the text.
