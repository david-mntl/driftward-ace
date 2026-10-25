# Drifters, the coin, view
Part of: drifters
Read when: you change how the coin looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/coin_view.py (DRA-62). Imports: pygame, core.drifters.base, core.drifters.coin,
# ui.drifters.registry. Never app.
COIN_LIT_COLOR: Final[tuple[int, int, int]] = (200, 30, 90)     # drifters/04-coin.md, palette: crystal lit side (guess)
COIN_SHADE_COLOR: Final[tuple[int, int, int]] = (70, 0, 60)     # same: crystal shade side
COIN_RIM_COLOR: Final[tuple[int, int, int]] = (255, 80, 150)    # same: ring and rim
COIN_GLINT_COLOR: Final[tuple[int, int, int]] = (255, 220, 240) # same: rare glint
COIN_LINE_WIDTH: Final[int] = 1    # drifters/04-coin.md, placeholder_look: the 1 px rim and the 1 px ring (guess)

@register_view(DrifterType.COIN)
def render_coin(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
                scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_coin draws a Coin") for any other drifter, and
    # ValueError("render_coin draws at full size only") when scale is not 1.0: a coin has no
    # entry warning, so render_drifter never asks for a smaller copy.
```

## Presentation

**Coin** (`render_coin`, DRA-62). Any drifter that is not a `Coin` raises `TypeError`; a `scale` other than 1.0 raises `ValueError`. Everything is drawn on whole pixels around `(cx, cy) = (round(center[0]), round(center[1]))`, with `half_width = round(obj.width / 2)` (6), `half_height = round(obj.height / 2)` (10) and `half_body = round(obj.body_height / 2)` (5). Each color goes through `dim_color(color, brightness)`. In this order (the pixel map is in Diagram, Coin):
1. **Lit side.** `pygame.draw.polygon` filled in `COIN_LIT_COLOR`, (200, 30, 90), through `(cx − 1, cy − half_height)`, `(cx − half_width, cy − half_body)`, `(cx − half_width, cy + half_body − 1)`, `(cx − 1, cy + half_height − 1)`: the left 6 columns, cx − 6 to cx − 1.
2. **Shade side.** The same in `COIN_SHADE_COLOR`, (70, 0, 60), through `(cx, cy − half_height)`, `(cx + half_width − 1, cy − half_body)`, `(cx + half_width − 1, cy + half_body − 1)`, `(cx, cy + half_height − 1)`: the right 6 columns, cx to cx + 5. Together the two halves are the crystal, columns cx − 6 to cx + 5 and rows cy − 10 to cy + 9: a 12 × 10 body from row cy − 5 to cy + 4 with a 5-row point above and below, each point 2 px wide at its tip.
3. **Rim.** `pygame.draw.polygon` with width `COIN_LINE_WIDTH` (1) in `COIN_RIM_COLOR`, (255, 80, 150), through the crystal's eight corners, clockwise from the top: `(cx − 1, cy − 10)`, `(cx, cy − 10)`, `(cx + 5, cy − 5)`, `(cx + 5, cy + 4)`, `(cx, cy + 9)`, `(cx − 1, cy + 9)`, `(cx − 6, cy + 4)`, `(cx − 6, cy − 5)` (written for the full-size numbers; in general from `half_width`, `half_height`, `half_body` as in steps 1 and 2). The point edges run at 45°, so every rim pixel lies on the crystal's outer pixels.
4. **Ring.** `pygame.draw.ellipse` with width `COIN_LINE_WIDTH` in `COIN_RIM_COLOR`, in the rect `(cx − obj.ring_width // 2, cy − obj.ring_height // 2, obj.ring_width, obj.ring_height)`: (cx − 11, cy − 4, 22, 8), columns cx − 11 to cx + 10, rows cy − 4 to cy + 3. Drawn over the crystal, so its top and bottom arcs cross the crystal's face.
5. **Glint**, only when `obj.glint`. `pygame.draw.rect` filled in `COIN_GLINT_COLOR`, (255, 220, 240), at `(cx − half_width + obj.glint_left, cy − half_height + obj.glint_top, obj.glint_size, obj.glint_size)`: (cx − 3, cy − 7, 2, 2). It lies in the left half of the top point, one pixel inside the rim and three rows above the ring. Drawn last, so it shows whole.
- Every pixel lies inside the crystal's `obj.width × obj.height` box and the ring's `obj.ring_width × obj.ring_height` box, both centered on `(cx, cy)`. Those are `obj.drawn_parts()` moved by the rounding (Rules, Coin, Drawn parts).
- Full size, common, at (440, 210): lit (200, 30, 90) in columns 435 to 439, shade (70, 0, 60) in 440 to 444, pink (255, 80, 150) on the outline (434 and 445 in the body's rows) and on the ring, which reaches columns 429 to 450 on rows 206 to 213; no (255, 220, 240) pixel. Rare: the same plus a (255, 220, 240) square on columns 437 to 438, rows 203 to 204.
- No galaxy core, no cloud, no swirl, no shine, no glint animation, no sound (scope report DRA-62, Limits and Out). The galaxy core color (15, 0, 20) in the palette is not drawn by the placeholder.
