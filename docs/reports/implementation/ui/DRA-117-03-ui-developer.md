Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-117-03 (Architect): the graze popup's color in `draw_points_popup` and the new `draw_graze_ring` view. Task: `docs/contracts/DRA-117/tasks/DRA-117-03-ui-developer.md`.

2. **Delivered:**
   - `game/ui/popup_view.py` (changed): `GRAZE_POPUP_COLOR`, color picked by `popup.kind`, text cache keyed by (points, kind).
   - `game/ui/graze_view.py` (new): `GRAZE_RING_COLOR`, `draw_graze_ring(surface, ring, ship)`, ring image cache.

3. **Checks:**
   - pygame-ce: `python -c "import pygame; assert pygame.IS_CE"` passes (2.5.8).
   - `python -m py_compile game/ui/popup_view.py game/ui/graze_view.py`: clean.
   - `game/tests/check.sh lint`: pass (ruff check and format). `typecheck`: pass (mypy strict, 97 files).
   - `check.sh ui`: 46 passed. `check.sh core`: 3160 passed, 1 failed (see Next): `tests/core/test_ufo.py::test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`. It is not in the `impact.md` table. It fails on `graze_state` SPENT != OUTSIDE after a touch, a core effect of DRA-117-02. Not caused by `game/ui/`.
   - Grep of the two files for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep `game/core` for `import ui` / `from ui`: no hits (the project imports `ui`, not `game.ui`).
   - Acceptance run. Script: `/tmp/claude-1000/-workspace/9cc7f9c9-8cf7-4368-8c43-83f4849aacad/scratchpad/dra117-03/check_draw.py` (kept outside the repo). Command, from `game/`:
     `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1 python /tmp/claude-1000/-workspace/9cc7f9c9-8cf7-4368-8c43-83f4849aacad/scratchpad/dra117-03/check_draw.py /tmp/claude-1000/-workspace/9cc7f9c9-8cf7-4368-8c43-83f4849aacad/scratchpad/dra117-03`
     PNGs (640 x 480, black, in that folder): `popups.png`, `ring_00.png` to `ring_14.png`. Output:
     ```
     coin popup   ink box (231, 235, 19, 8) height 8 max color (255, 80, 150) POPUP_COLOR (255, 80, 150)
     graze popup  ink box (391, 235, 19, 8) height 8 max color (255, 255, 255) GRAZE_POPUP_COLOR (255, 255, 255)
     same size: True
     age  0  diameter 16.00  ink radius  7  ink pixel (255, 255, 255)  ring_00.png
     age  1  diameter 17.07  ink radius  8  ink pixel (238, 238, 238)  ring_01.png
     age  2  diameter 18.13  ink radius  8  ink pixel (221, 221, 221)  ring_02.png
     age  3  diameter 19.20  ink radius  9  ink pixel (204, 204, 204)  ring_03.png
     age  4  diameter 20.27  ink radius  9  ink pixel (187, 187, 187)  ring_04.png
     age  5  diameter 21.33  ink radius 10  ink pixel (170, 170, 170)  ring_05.png
     age  6  diameter 22.40  ink radius 10  ink pixel (153, 153, 153)  ring_06.png
     age  7  diameter 23.47  ink radius 11  ink pixel (136, 136, 136)  ring_07.png
     age  8  diameter 24.53  ink radius 11  ink pixel (119, 119, 119)  ring_08.png
     age  9  diameter 25.60  ink radius 12  ink pixel (102, 102, 102)  ring_09.png
     age 10  diameter 26.67  ink radius 12  ink pixel (85, 85, 85)    ring_10.png
     age 11  diameter 27.73  ink radius 13  ink pixel (68, 68, 68)    ring_11.png
     age 12  diameter 28.80  ink radius 13  ink pixel (51, 51, 51)    ring_12.png
     age 13  diameter 29.87  ink radius 14  ink pixel (34, 34, 34)    ring_13.png
     age 14  diameter 30.93  ink radius 14  ink pixel (17, 17, 17)    ring_14.png
     after draw 1: CacheInfo(hits=0, misses=1, maxsize=None, currsize=1)
     after draw 2: CacheInfo(hits=1, misses=1, maxsize=None, currsize=1)
     cache ok: second draw built no surface
     core objects unchanged after draw
     ```
   - What it shows: the coin popup (+25 at x 240) is pink (255, 80, 150), the graze popup (same points, x 400) is `GRAZE_POPUP_COLOR`, and both ink boxes are 19 x 8, so the text size is the same. The ring, around a ship at (320, 240): the ink radius grows with age (7 to 14 px) and the ink pixel fades from (255, 255, 255) to (17, 17, 17) at every state. The radius is rounded to whole px, so it steps up every second state while the fade steps on every state. The first state's ink radius is 7 because pygame's circle of radius 8 and width 1 puts its outer pixel 7 px from the center. The second draw at one age is a cache hit with no new surface. The ring and ship objects are equal before and after a draw (they are frozen dataclasses).

4. **Assumptions:**
   - The ring image is a `2 * radius + 1` px square with the circle on its middle pixel, so the blit centers on `(round(ship.x), round(ship.y))` exactly.
   - The popup color table is a private dict keyed by `PopupKind`, so a new kind fails loudly with a `KeyError` instead of drawing in a wrong color.
   - Both graze colors are (255, 255, 255), the GDD values (guess).

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-117/tasks/DRA-117-03-ui-developer.md`. Failing core test for QA and the Architect, not for me: `test_ufo.py::test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds` compares whole Ufo objects after a touch, and the Ufo now carries `graze_state` SPENT. `impact.md` says QA reports such a test against its table and DRA-117-05 fixes it. Left alone: `game/ui/hud.py`, `score_text.py` (DRA-117-04), `game/app/` (the draw call is the Integration Engineer's).

7. **Status:** done.

## Decisions
- `draw_points_popup` keeps its signature. The color comes from `popup.kind` through one table, `_KIND_COLORS`. Source: run.md, Interface and Rationale ("Popups have a kind; colors stay in the view").
- The text cache is `_popup_surface(points, kind)`, as the contract says "once per (points, kind)". The font cache is unchanged, so both kinds share one font and one size (`POPUP_FONT_SIZE`).
- Ring look: circle outline of radius `round(ring.diameter / 2)`, width `ring.line_width`, alpha `round(255 * ring.opacity)`, on an SRCALPHA surface kept per (radius, width, alpha) with `functools.cache`, as `popup_view` does. Source: run.md, Presentation, Graze ring.
- The view reads the ship's center on every draw and stores nothing. `MAX_ALPHA` (255) names the alpha scale. The colors and every number about the ring come from core (`GrazeRing`) or the GDD (`graze_ring_color`, `graze_popup_color`, both guess).
- The view never draws when a ring is absent. Core drops finished rings, so no end test is in the view.
