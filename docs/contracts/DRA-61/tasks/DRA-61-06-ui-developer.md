Feature: DRA-61
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/hud.md
Status: done
Linear: DRA-68

## Read in the contract
- Purpose; Diagram (normal and debug mode, the flowchart).
- Interface: `game/ui/hud.py`, and `game/ui/score_text.py` (already built).
- Presentation: the `run.score` row; SCORE line; Both.
- Rules (all of it).
- Impact: the DRA-61 table.
- Rationale: the DRA-61 lines.

## Builds
- `game/ui/hud.py` (changed)

## Depends on
DRA-61-01, DRA-61-02, DRA-61-05

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
pygame.init()
from core.run import Run
from core.scroll import Scroll
from core.ship import spawn
from ui.hud import draw_hud
surface = pygame.Surface((640, 480))
draw_hud(surface, Run(ship=spawn(), scroll=Scroll(ticks=130, scrolled_ticks=100), lives=0), False)
ink = [(x, y) for y in range(480) for x in range(640) if tuple(surface.get_at((x, y)))[:3] != (0, 0, 0)]
print(min(x for x, _ in ink) >= 4, min(y for _, y in ink) >= 4, max(y for _, y in ink) < 24)
"
```
It prints `True True True`: all HUD ink sits on line 1, from the left margin and the top at 4 px, and nothing is drawn on line 2 (no `11 m`).

Also save one 640 × 480 PNG outside the repo with `draw_debug_overlay(surface, spawn())` then `draw_hud(..., lives=3)` and `below_overlay=True`: it shows `SCORE 11` below the green overlay text and three hearts at the top right. Put the command, the output and the image path in the implementation report.

`game/tests/check.sh` ends with `QA: pass`: lint, typecheck and every existing test pass, the two HUD tests reworded by task DRA-61-05 included.

## Out of scope
- `score_text` (task DRA-61-02) and the Game Over box (task DRA-61-03).
- LV, GRAZE, BEST, score popups, any new debug overlay content.
- Moving the HUD off the corner warnings (Director override, scope report DRA-61, Out).
- Core, app and test files; `ui/debug_overlay.py`.
