# Drifters, the meteorite, view
Part of: drifters
Read when: you change how the meteorite looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/meteorite_view.py. Imports: pygame, core.drifters.base, ui.drifters.registry. Never app.
METEORITE_COLOR: Final[tuple[int, int, int]] = (
    140,
    140,
    140,
)  # drifters/01-meteorite.md, placeholder_look (guess)


@register_view(DrifterType.METEORITE)
def render_meteorite(
    surface: pygame.Surface,
    obj: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None: ...
```

## Presentation

**Meteorite** (`render_meteorite`). A filled circle in `dim_color(METEORITE_COLOR, brightness)`, (140, 140, 140) at full brightness, as wide as `obj.width × scale`: center `(round(center[0]), round(center[1]))`, radius `round(obj.width * scale / 2)`. Full size: radius 10, 14, 20 for small, medium, big. Source: drifters/01-meteorite.md, placeholder_look, variants (guess).
