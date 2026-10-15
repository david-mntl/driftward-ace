Feature: DRA-23
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/run.md#presentation
Status: done
Linear: DRA-26

## Do
Build the Game Over box, a temporary stand-in.
- `game/ui/game_over.py` (new), exactly the `ui/game_over.py` block of `docs/contracts/systems/run.md`, Interface and Presentation:
  - Constants, each docstring saying: scope report DRA-23, Game Over box, temporary stand-in approved by the Director, not in the GDD (UI-04 is TBD). `BOX_SIZE = (320, 120)`, `BOX_COLOR = (0, 0, 0, 90)`, `TEXT_COLOR = (255, 255, 255)`, `TITLE_TEXT = "Game Over"`, `TITLE_FONT_SIZE = 32`, `PROMPT_TEXT = "Press any arrow to retry"`, `PROMPT_FONT_SIZE = 16`.
  - `draw_game_over(surface: pygame.Surface) -> None`:
    - The box: a 320 × 120 `pygame.SRCALPHA` surface filled with `BOX_COLOR`, no border, blitted with its top-left at `((width - 320) // 2, (height - 120) // 2)` from `surface.get_size()`.
    - The title: default font at 32 px, antialiased, `TEXT_COLOR`, centered horizontally.
    - The prompt: default font at 16 px, antialiased, `TEXT_COLOR`, centered horizontally, its top one title `get_linesize()` below the title's top.
    - The two-line block (title `get_linesize()` + prompt font `get_height()`) centered vertically in the box: `title_top = box_top + (120 - block_height) // 2`.
  - Build the box surface, both fonts and both rendered texts once, on the first draw, and keep them. Never per frame.
  - The view only draws. Don't fill the background, don't flip, don't log per frame, don't catch errors, don't read the run mode or a key.
- Imports in `game_over.py`: pygame only. Never `core`, never `app`.
- Follow game/CONTEXT.md: the module logger, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` before handoff.
- This task needs nothing from DRA-23-01 or DRA-23-02. It can start at once.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that saves two 640×480 PNGs outside the repo:
1. Fill with `ui.look.BACKGROUND`, `draw_starfield(surface, Scroll(ticks=130, scrolled_ticks=100))`, then `draw_game_over(surface)`. The image shows the stars, dimmer inside a 320 × 120 area in the middle, with white "Game Over" and the smaller "Press any arrow to retry" below it, both centered.
2. Fill the whole surface with (90, 100, 140), then `draw_game_over(surface)`.

From image 2 the script prints the color at (165, 185), inside the box away from the text, which is darker, about (58, 65, 91); the color at (100, 100), outside the box, which is still (90, 100, 140); and the bounding box of the (255, 255, 255) pixels, which lies inside x 160 to 479, rows 180 to 299. Put the command, the printed lines and both image paths in the implementation report.

## Out of scope
- Deciding when the box shows, and the draw order. The app calls `draw_game_over` while `run.game_over` is True; that is in `game/app/`, built by the Integration Engineer.
- A score or best score on the box. Out of DRA-23 scope.
- The hearts (task DRA-23-02).
- Any change to `game/core/`, `game/app/`, `game/main.py` or any other file in `game/ui/`.
- Tests.
