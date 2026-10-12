Feature: DRA-13
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-13/DRA-13-scroll.md#presentation
Status: done
Linear: DRA-15

## Do
Build the starfield view, exactly as the contract's Interface (the `ui/starfield.py` block) and Presentation sections give it, in `game/ui/starfield.py`.
- `STAR_COUNT = 50`, `STAR_COLOR = (90, 100, 140)`, `STAR_SIZES = (1, 2)`. Each docstring says: scope report DRA-13, temporary stand-in approved by the Director, not in the GDD.
- `STAR_SEED`: pick any fixed int once and keep it. It only makes the layout the same every run.
- `STARS`: built once with `random.Random(STAR_SEED)`. For each of the 50 stars, in this order: `x = rng.randrange(SCREEN_W)`, `base_y = rng.randrange(SCREEN_H)`, `size = rng.choice(STAR_SIZES)`. `SCREEN_W` and `SCREEN_H` from `core.world`.
- `draw_starfield(surface: pygame.Surface, scroll: Scroll) -> None`: for each star, a filled `size` × `size` square in `STAR_COLOR` with its top-left at `(x, int((base_y + scroll.distance_px) % SCREEN_H))`.
- Read only `scroll.distance_px`. Don't fill the background, don't flip, don't log per frame, don't change the scroll, don't read the run mode or any key.
- Imports: pygame, random, `core.scroll`, `core.world`. Never `app`.
- Follow game/CONTEXT.md: the module logger, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` before handoff.
- This task needs `game/core/scroll.py` from task DRA-13-01. Start after it is built.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that fills a 640×480 surface with `ui.look.BACKGROUND`, calls `draw_starfield(surface, start_scroll())`, and saves it as a PNG outside the repo. Then do the same with `Scroll(ticks=40, scrolled_ticks=10)` (11 px of scroll) as a second PNG. The first image shows about 50 dim (90, 100, 140) dots, 1 or 2 px each, spread over the whole screen. The second shows the same pattern 11 px lower, with the dots that were in the bottom 11 rows now at the top. Put the command and both image paths in the implementation report.

## Out of scope
- Calling the view each frame and the draw order. These are in `game/app/`, built by the Integration Engineer.
- The HUD (task DRA-13-03).
- Parallax, more layers, twinkle, a picture background. Out of DRA-13 scope.
- Any change to `game/core/`, `game/app/`, `game/main.py`, or any other file in `game/ui/`.
- Tests.
