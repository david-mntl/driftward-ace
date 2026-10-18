Feature: DRA-61
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/hud.md
Status: done
Linear: DRA-65

## Read in the contract
- run.md: Interface, `game/ui/game_over.py` (`SCORE_FONT_SIZE`, `draw_game_over`, `draw_final_score`).
- run.md: Presentation: the `run.game_over` and `run.score` rows, and the list under them (the paragraph naming what each function draws; Box, Title, Score, Prompt, Vertical place, Width, and the build-once line).
- run.md: Rules, Values (the score line's source).
- run.md: Impact, the DRA-61 table; Rationale, the DRA-61 lines on the Game Over box and on `draw_final_score`.
- hud.md: Interface, `game/ui/score_text.py`; Presentation, `score_text(score)`.

## Builds
- `game/ui/game_over.py` (changed)

## Depends on
DRA-61-02

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
pygame.init()
from ui.game_over import draw_game_over, draw_final_score
def white(score):
    surface = pygame.Surface((640, 480))
    draw_game_over(surface)
    if score is not None:
        draw_final_score(surface, score)
    return [(x, y) for y in range(480) for x in range(640) if tuple(surface.get_at((x, y)))[:3] == (255, 255, 255)]
def bands(points):
    rows = sorted({y for _, y in points})
    groups = [[rows[0]]]
    for row in rows[1:]:
        if row == groups[-1][-1] + 1:
            groups[-1].append(row)
        else:
            groups.append([row])
    return groups
def width(points, band):
    columns = [x for x, y in points if y in band]
    return max(columns) - min(columns)
bare, small, big = white(None), white(0), white(1234567)
print(len(bands(bare)), len(bands(small)), len(bands(big)))
print(width(big, bands(big)[1]) > width(small, bands(small)[1]))
print(all(160 <= x < 480 and 180 <= y < 300 for x, y in big))
print(bands(bare)[0] == bands(big)[0] and bands(bare)[1] == bands(big)[2])
"
```
It prints four lines:
- `2 3 3`: the box alone has two lines of text, title and prompt; with the score line, three.
- `True`: the middle line is the score, wider for `SCORE 1 234 567` than for `SCORE 0`.
- `True`: every text pixel is inside the box.
- `True`: the title and the prompt sit on the same rows with or without the score line.

Also save one 640 × 480 PNG outside the repo of `draw_game_over(surface)` then `draw_final_score(surface, 1234)`: it shows "Game Over", `SCORE 1 234` and "Press any arrow to retry", centered. Put the command, the output and the image path in the implementation report.

`game/tests/check.sh` ends with `QA: pass`: lint, typecheck and every existing test pass. Typecheck stays clean because `game/app/frame.py`'s `draw_game_over(surface)` call is unchanged and still valid (run.md, Impact).

## Out of scope
- The `frame.py` call to `draw_final_score`: the Integration Engineer's.
- A redesign of the Game Over box (UI-04): box size, color, title and prompt stay as they are.
- The HUD and `score_text` (tasks DRA-61-06 and DRA-61-02).
- Core, app and test files.
