# Drifters, the satellite, view
Part of: drifters
Read when: you change how the satellite looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/satellite_view.py (DRA-39). Imports: pygame, core.collision, core.drifters.base,
# ui.shapes, ui.drifters.registry. Never app.
SATELLITE_BODY_COLOR: Final[tuple[int, int, int]] = (
    240,
    240,
    240,
)  # drifters/02-satellite.md, placeholder_look (guess)
SATELLITE_PANEL_COLOR: Final[tuple[int, int, int]] = (60, 110, 220)  # same


@register_view(DrifterType.SATELLITE)
def render_satellite(
    surface: pygame.Surface,
    obj: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None: ...
```

## Presentation

**Satellite** (`render_satellite`, DRA-39). The satellite's two hitbox boxes, filled, upright, never turned (the satellite never rotates; only its warning copy is tilted). `obj.hitbox[0]` is the body and `obj.hitbox[1]` the panel bar: the satellite's tuning lists them in that order (`docs/contracts/schemas/satellite-tuning.schema.json`). Each box is drawn with `ui.shapes.draw_shape(surface, color, Box(center[0] + box.cx * scale, center[1] + box.cy * scale, box.w * scale, box.h * scale))`, so the full-size look sits exactly on the debug outlines. First the panel bar in `dim_color(SATELLITE_PANEL_COLOR, brightness)`, (60, 110, 220) at full brightness, then the body on top in `dim_color(SATELLITE_BODY_COLOR, brightness)`, (240, 240, 240). Full size: a 36 × 6 blue bar with a 12 × 12 white square over its middle. Half size: 18 × 3 and 6 × 6. A hitbox that isn't two boxes raises `TypeError`. Source: drifters/02-satellite.md, placeholder_look, size, hitbox, rule 8 (guess).
