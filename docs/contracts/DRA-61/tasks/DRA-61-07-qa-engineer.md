Feature: DRA-61
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/hud.md
Status: open
Linear: DRA-69

## Read in the contract
- Interface, `game/ui/hud.py`.
- Presentation: the `run.score` and `run.lives` rows; SCORE line; Hearts; Both.
- Rules (all of it).
- Impact, the DRA-61 table, the `game/tests/ui/test_hud.py` row.

## Builds
- `game/tests/ui/test_hud.py` (changed)

## Depends on
DRA-61-06

## Not in the contract
- As `test_hud.py` does today, read positions from the drawn pixels and assert the `ui` constants against the scope reports' numbers. Source: tests/CONTEXT.md, Rules.

## Test
- SCORE is drawn on HUD line 1 at the left margin, in both modes, and its pixels change when the score changes. Presentation, SCORE line; Rules.
- Nothing is drawn on HUD line 2: the meters readout is gone. Presentation, SCORE line; Rules.
- In debug mode SCORE's top is exactly at the overlay's bottom plus the gap. Presentation, SCORE line.
- The earlier HUD behaviors still hold with SCORE: no overlap with the overlay, no jump when F3 hides it, above the top line, the hearts. Rules; Presentation, Hearts.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the SCORE line tests in `test_hud.py` in the `ui` step.

## Out of scope
- `score_text` and the Game Over box (task DRA-61-05).
- The score rule in core (task DRA-61-04).
- The corner warnings under the HUD (Director override).
- The draw order and the `frame.py` calls in `game/app/`. `check.sh` has no `app` step.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py` or game code.
