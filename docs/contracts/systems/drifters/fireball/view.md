# Drifters, the fireball, view
Part of: drifters
Read when: you change how the fireball looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/fireball_view.py (DRA-56). Imports: pygame, core.collision, core.drifters.base,
# ui.shapes, ui.drifters.registry. Never app.
FIREBALL_HEAD_COLOR: Final[tuple[int, int, int]] = (255, 140, 0)   # drifters/06-fireball.md, placeholder_look (guess)
FIREBALL_TAIL_COLOR: Final[tuple[int, int, int]] = (200, 160, 0)   # same

@register_view(DrifterType.FIREBALL)
def render_fireball(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
                    scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_fireball draws two circles, head then tail") when obj.hitbox is not
    # exactly two Circles.
```

## Presentation

**Fireball** (`render_fireball`, DRA-56). The fireball's two hitbox circles, filled. `obj.hitbox[0]` is the head and `obj.hitbox[1]` the tail (`fireball_hitbox` builds them in that order); a hitbox that isn't exactly two `Circle`s raises `TypeError`. Each circle `c` is drawn with `ui.shapes.draw_shape(surface, color, Circle(center[0] + c.cx × scale, center[1] + c.cy × scale, c.r × scale))`, so the full-size look sits exactly on the debug outlines. First the tail in `dim_color(FIREBALL_TAIL_COLOR, brightness)`, (200, 160, 0) at full brightness, then the head on top in `dim_color(FIREBALL_HEAD_COLOR, brightness)`, (255, 140, 0). The tail lies behind the head along the path, so the look points the way it flies. Full size, small: an orange disc of radius 10 (21 px across) with a dark yellow disc of radius 5 touching it up and to the left (up and to the right with `invert`), its center 9.03 px left and 12.90 px up. Big: radius 16 and 8. Source: drifters/06-fireball.md, placeholder_look, hitbox, size (guess); 07-drifters.md, rule 8.
- In the entry warning the view draws `obj.warning_copy()`: the comet laid straight down, the tail above the head, 3 × R long, scaled to 14 px (scale 14 / 31.5 small, 14 / 48 big). At that scale both variants draw the same: a head of radius 5 whose center sits 2.33 px below the copy's center, and a tail of radius 2 whose center sits 4.67 px above it. The entry warning then turns it by `obj.warning_tilt_degrees()`: 35° counterclockwise, so the head points down and to the right, or 35° clockwise with `invert`, so it points down and to the left. Source: drifters/06-fireball.md, rule 1; 07-drifters.md, entry_warning_size.
- No trail, no sprite, no glow, no sound (scope report DRA-56, Out).
