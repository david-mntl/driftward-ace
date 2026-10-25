# Drifters, the floating island, view
Part of: drifters
Read when: you change how the floating island looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/floating_island_view.py (DRA-86). Imports: pygame, core.collision,
# core.drifters.base, core.drifters.floating_island, ui.shapes, ui.drifters.registry. Never app.
ISLAND_FILL_COLOR: Final[tuple[int, int, int]] = (70, 160, 80)   # drifters/05-floating-islands.md, placeholder_look (guess)
ISLAND_EDGE_COLOR: Final[tuple[int, int, int]] = (35, 90, 45)    # same: the darker edge
ISLAND_EDGE_WIDTH: Final[int] = 2  # same: the edge is 2 px, drawn inside the shape (guess)

@register_view(DrifterType.FLOATING_ISLAND)
def render_floating_island(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
                           scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_floating_island draws a FloatingIsland") for any other drifter, and
    # ValueError("render_floating_island draws at full size only") when scale is not 1.0: an
    # island has no entry warning, so render_drifter never asks for a smaller copy.
```

## Presentation

**Floating island** (`render_floating_island`, DRA-86). Any drifter that is not a `FloatingIsland` raises `TypeError`; a `scale` other than 1.0 raises `ValueError`. The look is one image per island look, built once and blitted each frame:
- **Image.** A `pygame.SRCALPHA` surface of `round(obj.width) × round(obj.height)`, fully transparent, kept in a dict keyed by `(obj.hitbox, obj.width, obj.height, brightness)` (the hitbox already holds `invert`). Built the first time that key is drawn, never rebuilt, never per frame. With `(hw, hh) = (obj.width / 2, obj.height / 2)`, in this order:
  1. **Edge.** Every shape of `place_hitbox(obj.hitbox, hw, hh)`, filled with `ui.shapes.draw_shape(image, dim_color(ISLAND_EDGE_COLOR, brightness), shape)`: (35, 90, 45) at full brightness. This is the whole shape.
  2. **Fill.** Every shape of the inset hitbox, placed the same way, filled in `dim_color(ISLAND_FILL_COLOR, brightness)`: (70, 160, 80). With `e = ISLAND_EDGE_WIDTH` (2): a `Box(cx, cy, w, h)` insets to `Box(cx, cy, w − 2e, h − 2e)`; a `Polygon` insets to the polygon whose every edge line is moved `e` px toward the inside along its inward unit normal, its corner `i` where the moved lines of edges `i − 1` and `i` meet.
  So the edge is every pixel of the shape that no inset shape covers: 2 px along every outer side, and never along the seam where the L's or the T's two boxes overlap (their insets overlap there too). Source: drifters/05-floating-islands.md, placeholder_look ("a 2 px edge ... drawn inside the shape", guess); scope report DRA-86, Limits ("The edge never draws outside the hitbox").
- **Place.** The image's top-left at `(round(center[0] − obj.width / 2), round(center[1] − obj.height / 2))`. The sizes are even whole px, so this is the rounded center minus the half size, and every box edge and triangle corner lands on a whole px. Every pixel lies inside the footprint `Box(x, y, width, height)` moved by the center's rounding, which is at most 0.5 px: those are `obj.drawn_parts()` (Rules, Floating island, Drawn parts).
- **Examples**, full size, centered at (320, 300), footprint columns 160 to 479 and rows 240 to 359:
  - rectangle: (35, 90, 45) on columns 160, 161, 478, 479 and on rows 240, 241, 358, 359; (70, 160, 80) at every pixel of columns 162 to 477 and rows 242 to 357, e.g. (320, 300). Nothing drawn at (159, 300) or (320, 360).
  - l_shape: the upright is columns 160 to 199, the bar rows 320 to 359. (199, 250) and (198, 320) are edge; (198, 330) and (300, 340) are fill; (200, 250) is not drawn (inside the L's notch). With `invert`: the bar is rows 240 to 279, and (300, 250) is fill, (300, 300) not drawn.
  - t_shape: the bar is rows 240 to 279, the stem columns 300 to 339. (320, 330) is fill, (301, 330) edge, (250, 330) not drawn.
  - triangle: row 240 has one pixel, (160, 240), edge. Row 355 runs from column 160 to 467: (461, 355) fill, (462, 355) to (467, 355) edge, (468, 355) not drawn. Row 359 runs from 160 to 478, all edge. (170, 350) is fill. With `invert`, the same mirrored top to bottom: row 359 has one pixel, (160, 359); row 244 (the mirror of 355) runs from 160 to 467.
- No grass, no rock texture, no shadow, no sound (scope report DRA-86, Out: final art and sound).
