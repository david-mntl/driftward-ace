Feature: DRA-76
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/debug-overlay.md
Status: open
Linear: DRA-82

## Read in the contract
- Purpose.
- Diagram: the flowchart (the wave lines) and the six text lines.
- Interface: `OVERLAY_TEXT_LINES`, `draw_debug_wave_lines`, `overlay_text_bottom`.
- Presentation: the `overlay_text_bottom()` bullet; the `draw_debug_wave_lines` table and the bullets under it; the hitboxes' draw-order bullet.
- Rules: all of them.
- Impact, the DRA-76 table. Rationale, the DRA-76 lines and "Every fact the overlay shows is a core field".
- To read only: `docs/contracts/systems/waves.md`, Presentation; `docs/contracts/systems/run.md`, Interface (`waves`, `level`).

## Builds
- `game/ui/debug_overlay.py` (changed)

## Depends on
DRA-76-05

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
from dataclasses import replace
import pygame
pygame.init()
from core.run import start_run
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, start_waves
from ui.debug_overlay import OVERLAY_COLOR, OVERLAY_MARGIN, draw_debug_wave_lines, overlay_text_bottom
font = pygame.font.Font(None, 16)
line = font.get_linesize()
w0 = Wave(wave_id='wave_0', length_px=100.0, kind=WaveKind.FIXED, min_level=None)
book = WaveBook(waves={'wave_0': w0}, wave_zero_id='wave_0', playlists=tuple(LevelPlaylist() for _ in range(8)))
playing = start_run(waves=start_waves(book, 1))
resting = replace(playing, waves=replace(playing.waves, resting=True, rest_ticks_left=5, level=3))
def drawn(run):
    surface = pygame.Surface((640, 480))
    draw_debug_wave_lines(surface, run)
    return pygame.image.tobytes(surface, 'RGB')
def expected(wave_text, level_text):
    surface = pygame.Surface((640, 480))
    surface.blit(font.render(wave_text, True, OVERLAY_COLOR), (OVERLAY_MARGIN, OVERLAY_MARGIN + 4 * line))
    surface.blit(font.render(level_text, True, OVERLAY_COLOR), (OVERLAY_MARGIN, OVERLAY_MARGIN + 5 * line))
    return pygame.image.tobytes(surface, 'RGB')
print(drawn(start_run()) == expected('wave none', 'level 1'), drawn(playing) == expected('wave wave_0', 'level 1'), drawn(resting) == expected('wave rest', 'level 3'))
print(overlay_text_bottom() == OVERLAY_MARGIN + 5 * line + max(line, font.get_height()))
"
```
It prints `True True True`, then `True`: lines 5 and 6 read `wave none` with no waves, `wave <id>` while a wave plays and `wave rest` during a rest, with the level under them, right under line 4; and the overlay's bottom covers six lines.

Put the command and its output in the implementation report. `game/tests/check.sh` ends `QA: pass`: `game/tests/ui/test_hud.py` passes unchanged.

## Out of scope
- `draw_debug_overlay` and `draw_debug_hitboxes`: no change to what they draw.
- `game/ui/hud.py` (it reads `overlay_text_bottom()` already), calling the new function from `game/app/frame.py` (Integration Engineer), core, tests.
- The level on the HUD.
