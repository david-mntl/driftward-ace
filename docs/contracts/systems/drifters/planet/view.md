# Drifters, the planet, view
Part of: drifters
Read when: you change how the planet looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/planet_view.py (DRA-96). Imports: pygame, math, core.drifters.base,
# core.drifters.planet, ui.drifters.registry. Never app.
PLANET_BODY_COLOR: Final[tuple[int, int, int]] = (140, 70, 200)   # drifters/08-planet.md, placeholder_look (guess)
PLANET_RING_COLOR: Final[tuple[int, int, int]] = (180, 120, 255)  # same: every field ring
PLANET_RING_WIDTH: Final[int] = 1  # same: every field ring is 1 px (guess)

@register_view(DrifterType.PLANET)
def render_planet(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
                  scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_planet draws a Planet") for any other drifter.
```

## Presentation

**Planet** (`render_planet`, DRA-96). Any drifter that is not a `Planet` raises `TypeError`. Everything is drawn around `(cx, cy) = (round(center[0]), round(center[1]))`, and each color goes through `dim_color(color, brightness)`.
- **Full size** (`scale` 1.0, the planet ACTIVE), in this order:
  1. **Outer ring.** `pygame.draw.circle(surface, dim_color(PLANET_RING_COLOR, brightness), (cx, cy), round(obj.pull_radius), PLANET_RING_WIDTH)`: a 1 px ring in (180, 120, 255) at full opacity. It shows where the pull starts. Source: placeholder_look ("a 1 px ring at `pull_radius`"); rule 2.
  2. **Inner rings.** For each `ring` in `obj.inner_rings()`, in order: a 1 px circle of radius `round(ring.radius)` around the same center, in `dim_color(PLANET_RING_COLOR, brightness)` with alpha `math.floor(255 × ring.opacity + 0.5)`, blended over what is beneath it. A ring whose alpha is 0 is not drawn. They are drawn on one `pygame.SRCALPHA` layer of side `2 × (round(obj.pull_radius) + 1) + 1`, centered on `(cx, cy)`: the layer is kept in a dict keyed by its side, built the first time that side is drawn, and on every frame cleared to fully transparent, drawn on (each ring centered on the layer's middle pixel) and blitted once. Never a new surface per frame. At the file's values, on the state the planet turns ACTIVE: one ring at radius 150, alpha 128, over the outer ring, and one at radius 91, alpha 64. Source: placeholder_look ("two faint 1 px rings that drift inward from it and fade"); field_ring_trip, field_ring_gap, field_ring_fade (guess); 91-decision-log.md, row 76.
  3. **Body.** A filled circle in `dim_color(PLANET_BODY_COLOR, brightness)`, (140, 70, 200) at full brightness, center `(cx, cy)`, radius `round(obj.width × scale / 2)`: 32. Drawn last, over the rings. Its look fills the hitbox circle. Source: placeholder_look; size, hitbox (guess); rule 10 ("Every skin fills the hitbox circle exactly").
- **Smaller** (`scale` below 1.0: the entry warning's copy, the planet in WARNING): the body only, radius `round(obj.width × scale / 2)`: at the warning's scale 14 / 64 a purple disc of radius 7. No ring: the field is on from the tick the planet appears, and at that scale the outer ring (radius about 33) would lie outside the 25 px warning image anyway. Source: rule 1 ("Its field is on from the tick it appears"); 07-drifters.md, entry_warning_size.
- Every drawn pixel lies inside `obj.drawn_parts()` moved by the center's rounding (Rules, Planet, Drawn parts). The view never works out where a ring is: radii and opacities come from core.
- Full size, at (320, 300), full brightness, on its first ACTIVE state: (140, 70, 200) at (320, 300) and at (300, 300); (180, 120, 255) on the ring 150 px out, within 1 px of (320, 150), (470, 300), (320, 450) and (170, 300); a blend of (180, 120, 255) over the background within 1 px of (320, 209) and (229, 300), the inner ring at 91; nothing drawn at (320, 140) or (320, 230) but the background. During the re-hit cooldown: (105, 53, 150) at (320, 300) and (135, 90, 191) on the outer ring.
- No sphere shading, no glow, no pulse, no sound (scope report DRA-96, Out: final art and sound).
