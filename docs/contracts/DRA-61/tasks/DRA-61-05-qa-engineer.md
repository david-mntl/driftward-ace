Feature: DRA-61
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/hud.md, docs/contracts/systems/run.md
Status: open
Linear: DRA-67

## Read in the contract
- hud.md: Interface, `game/ui/score_text.py`; Presentation, `score_text(score)`.
- hud.md: Presentation, SCORE line (the `hud_top` lines); Impact, the DRA-61 table, the `game/tests/ui/test_hud.py` row (the two tests and what they are reworded to); Rationale, the DRA-61 line on the HUD tests changing in two steps.
- run.md: Interface, `game/ui/game_over.py`; Presentation, the `run.game_over` row and the list under it (what each function draws; Box, Title, Score, Prompt, Vertical place, Width).

## Builds
- `game/tests/ui/test_score_text.py` (new)
- `game/tests/ui/test_game_over.py` (new)
- `game/tests/ui/test_hud.py` (changed)

## Depends on
DRA-61-02, DRA-61-03

## Not in the contract
- As `test_hud.py` does today, read positions from the drawn pixels and assert the `ui` constants against the scope reports' numbers. Source: tests/CONTEXT.md, Rules.
- At this point `game/ui/hud.py` still draws the meters readout on line 2; the SCORE line comes in task DRA-61-06. The two reworded HUD tests must pass now and after it. Source: hud.md, Impact.

## Test
- `score_text` gives `SCORE`, a space, then the digits in groups of three split by one space, no leading zeros, no digit limit: the scope report's four examples, a group of zeros inside the number, and a number far past a million. hud.md: Presentation, `score_text(score)`.
- `draw_game_over` then `draw_final_score` shows three centered lines inside the box, the middle one the given score's text, and only that line changes with the score. run.md: Presentation, `draw_game_over` and `draw_final_score` (Score, Vertical place).
- `draw_game_over` alone shows the title and the prompt in the same places as with the score line, and nothing in the score line's place. run.md: Presentation, Vertical place.
- In normal mode the HUD's ink starts at or right of the left margin and at or below the HUD top. Replaces `test_hud_normal_layout_leaves_line_one_empty`. hud.md: Impact, the `test_hud.py` row; Presentation, SCORE line.
- In debug mode the HUD's first ink is at or below the overlay's bottom plus the gap. Replaces the line-2 offset in `test_hud_keeps_the_gap_below_the_overlay`. hud.md: Impact, the `test_hud.py` row; Presentation, SCORE line.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_score_text.py`, `test_game_over.py` and the reworded `test_hud.py` in the `ui` step.

## Out of scope
- The score rule in core (task DRA-61-04).
- The SCORE line's own tests: line 1, line 2 empty, the exact debug-mode place (task DRA-61-07).
- The corner warnings under the HUD (Director override).
- The draw order and the `frame.py` calls in `game/app/`. `check.sh` has no `app` step.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py` or game code.
