Feature: DRA-62
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/run.md
Status: open
Linear: DRA-73

## Read in the contract
- Interface, `game/core/popup.py`: `PointsPopup` and its `y` (to read; built by DRA-62-01).
- Interface, `game/ui/popup_view.py` (all of it).
- Presentation: the `run.popups` row; Points popup (all of it).
- Diagram: the popup timeline (what the view is given on each state).
- Impact, the DRA-62 table (the `popup_view.py` row). Rationale, the DRA-62 lines on popups.

## Builds
- `game/ui/popup_view.py` (new)

## Depends on
DRA-62-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
from core.popup import PointsPopup
from ui.popup_view import POPUP_COLOR, POPUP_FONT_SIZE, draw_points_popup, popup_text
pygame.init()
popup = PointsPopup(x=320.0, start_y=164.0, points=50, lifetime_ticks=60, rise_per_tick=0.5, age_ticks=30)
drawn = pygame.Surface((640, 480))
draw_points_popup(pygame.Surface((640, 480)), popup)
draw_points_popup(drawn, popup)
expected = pygame.Surface((640, 480))
text = pygame.font.Font(None, POPUP_FONT_SIZE).render(popup_text(50), True, POPUP_COLOR)
expected.blit(text, text.get_rect(center=(320, 149)))
print(popup_text(50), popup_text(100), pygame.image.tobytes(drawn, 'RGB') == pygame.image.tobytes(expected, 'RGB'))
"
```
It prints `+50 +100 True`: the text, in the popup color and the default font at 16 px, centered on the popup's place 30 ticks after it appeared, and the second draw (from the kept text) looks exactly like a fresh render. Put the command and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass.

## Out of scope
- Drawing the popups each frame and their layer: the Integration Engineer, from `docs/contracts/systems/app.md`.
- The coin's view (task DRA-62-03).
- Any core file, `game/app/`, tests.
- A fade, an outline, a shadow, sound.
