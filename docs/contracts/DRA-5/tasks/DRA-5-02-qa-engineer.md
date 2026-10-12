Feature: DRA-5
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/DRA-5/DRA-5-app.md#presentation
Status: done
Linear: DRA-8

## Do
Write permanent tests for the error screen in `game/tests/ui/test_error_screen.py`. Test through `draw_error_screen(surface, detail)` and `ui.look.BACKGROUND` only. Use the `pygame_headless` fixture and a 640×480 surface. A browser run can't trigger an unexpected error, so these tests are the only proof the screen works.

Test each behavior:
1. With `detail=None`, the surface is the background color everywhere except one line of white text, centered horizontally and vertically, and nothing is drawn below that line. Source: 10-ui.md, error_screen, error_layout, error_text_color. 12-art-and-audio.md, placeholder_bg.
2. With `detail="ValueError: boom"`, a second line of white text appears below the main line, centered horizontally, and the main line is unchanged. Source: 10-ui.md, error_layout, error_debug_line.
3. The background fully replaces what was on the surface before. Pre-fill the surface with another color, draw with `detail=None`, and check that a corner pixel is `BACKGROUND`. Source: 10-ui.md, rule 8 (the error screen replaces the game).

Every expected color comes from the GDD values named above. Read positions from the drawn pixels. Never hard-code the font's pixel size.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `ui` step runs the new tests in `tests/ui/test_error_screen.py`.

## Out of scope
- Run-mode parsing, logging setup and the guard in `game/app/`. `check.sh` has no `app` step, so the integration browser run covers them.
- The cut of a too-long detail. It can't be told apart from clipping by pixels alone, so the Implementation Reviewer checks it by reading the code.
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`.
