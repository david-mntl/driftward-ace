Feature: DRA-61
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/hud.md
Status: done
Linear: DRA-64

## Read in the contract
- Purpose (the `score_text` paragraph).
- Interface: `game/ui/score_text.py`.
- Presentation: `score_text(score)`.
- Impact: the DRA-61 table, the `game/ui/score_text.py` row.
- Rationale: the DRA-61 lines on "Core gives the number, UI gives the text", "The format has one home" and "No digit limit".

## Builds
- `game/ui/score_text.py` (new)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
import sys
from ui.score_text import score_text
print([score_text(n) for n in (0, 999, 1000, 1234, 1000007, 1234567)])
print('pygame' in sys.modules)
"
```
It prints two lines:
- `['SCORE 0', 'SCORE 999', 'SCORE 1 000', 'SCORE 1 234', 'SCORE 1 000 007', 'SCORE 1 234 567']`
- `False`: the module imports no pygame.

Put the command and its output in the implementation report. `game/tests/check.sh` ends with `QA: pass`: lint, typecheck and every existing test pass unchanged.

## Out of scope
- The HUD's SCORE line and `game/ui/hud.py` (task DRA-61-06).
- The Game Over box (task DRA-61-03).
- LV, GRAZE, BEST, score popups.
- Core, app and test files.
