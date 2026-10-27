Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the stand-in instructions page view, `draw_instructions`, from `docs/contracts/DRA-125/tasks/DRA-125-05-ui-developer.md` (Architect), against `docs/contracts/systems/game-flow.md`.

2. **Delivered:** `game/ui/instructions.py` (new): `INSTRUCTIONS_TITLE_TEXT`, `INSTRUCTION_SECTIONS`, `ICON_SIZE`, `ICON_LINE_WIDTH`, `draw_instructions(surface)`. Imports pygame and `ui.screen_look` only.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/instructions.py`: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 110 files already formatted.
   - Headless draw run, 640 x 480 surface filled with `ui.look.BACKGROUND`, then `draw_instructions`. Command (from `/workspace/game`): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python /tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/check_instr.py`. PNG saved to `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/instructions.png`. Ink rows and columns per row (body linesize 12, heading row 16 px, footer top 456):
     ```
     title            rows  98-114  cols 243-397  center 320.0
     heading FLY      rows 132-147  cols 300-338  center 319.0   icon cols 300-315
       line FLY       rows 148-158  cols 134-505  center 319.5
     heading PAUSE    rows 172-187  cols 291-347  center 319.0   icon cols 291-306
       line PAUSE     rows 188-198  cols 186-455  center 320.5
     heading GRAZE    rows 212-227  cols 290-348  center 319.0   icon cols 290-305
       line GRAZE     rows 228-238  cols 157-483  center 320.0
     heading WARNING  rows 252-267  cols 283-354  center 318.5   icon cols 283-298
       line WARNING   rows 268-278  cols 159-481  center 320.0
     heading FALL     rows 292-307  cols 296-342  center 319.0   icon cols 296-311
       line FALL      rows 308-318  cols 212-429  center 320.5
     heading COINS    rows 332-347  cols 291-346  center 318.5   icon cols 291-306
       line COINS     rows 348-358  cols 179-461  center 320.0
     footer           rows 457-466  cols 227-414  center 320.5
     ```
     Every row is centered on 320 (within 1.5 px, font side bearings), inside 0-479 and 0-639, and no band overlaps another. The six icons are 16 x 16 outlines, each left of its title. Sections are in the scope report's order and wording. The block runs rows 98-358, between the top and the footer (456).
   - Follows the state: the view takes no state. Two draws of the same surface give the same picture (all text is cached after the first draw). It touches no core object.
   - `game/tests/check.sh lint`: PASS (lint and format).
   - `typecheck`: 7 errors, all `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`: the first row of the impact.md table, cleared by DRA-125-09. None in `game/ui/instructions.py`.
   - `core`: 26 failed, 3205 passed. All are in `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py`, `test_run_waves.py`, the files and kinds of test that impact.md names for DRA-125-01 (the last life now ends on a later tick, no arrow retry, new log lines). I did not touch core or tests.
   - `ui`: 65 passed, unchanged.
   - Grep of `game/ui/instructions.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for `game.ui` or `ui` imports: no hits.

4. **Assumptions:**
   - The blank line under the title is one body line high, per the Presentation "Lines and blank lines" (a blank line is one body line's height). The menu's blank is a title line; the instructions page says only "a blank line".
   - The icon and the section title are centered vertically in the heading row by the icon's center and the rendered title's rect `centery`.
   - The title text `HOW TO PLAY` and the six section titles in capitals are as written in the scope report.
   - `ICON_LINE_WIDTH` is 1 px (contract Rationale: "A 1-px outline").

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-125/tasks/DRA-125-05-ui-developer.md`. Left alone: `game/ui/menu.py` has a private `_render` like this module's; a shared helper in `screen_look.py` would be DRA-125-04's file, so I kept both private. The leaderboard, pause box and game-over views are later tasks.

7. **Status:** done.

## Decisions
- Layout is worked from `get_linesize()` and `size(" ")` as the contract's Rationale asks. The heading row height is `max(ICON_SIZE, body linesize)` (16 px here). The line row follows it with no gap, and one blank body line separates sections.
- The footer top is `height - 2 * body_line`; the block is centered in `[0, footer_top]` with integer division.
- Texts are rendered once through a private `functools.cache` function (key: text and size), as in `ui/menu.py`. Fonts come from `screen_font`. The heading title and the icon are blitted separately so the icon is drawn with `pygame.draw.rect` and the width `ICON_LINE_WIDTH`.
- Sources: sizes, color, footer and back text from `ui.screen_look`; title, section pairs and `ICON_SIZE` from scope report DRA-125, Values needed (Instructions page); `ICON_LINE_WIDTH` from the contract, Presentation, Instructions page.
