# Drifters, the UFO, view
Part of: drifters
Read when: you change how the UFO looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/ufo_view.py (DRA-104). Imports: pygame, core.collision, core.drifters.base,
# ui.shapes, ui.drifters.registry. Never app.
UFO_DISC_COLOR: Final[tuple[int, int, int]] = (170, 170, 185)   # drifters/07-ufo.md, placeholder_look (guess)
UFO_DOME_COLOR: Final[tuple[int, int, int]] = (90, 220, 110)    # same

@register_view(DrifterType.UFO)
def render_ufo(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
               scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_ufo draws a box then a circle, disc then dome") when obj.hitbox is
    # not exactly a Box followed by a Circle.
```

## Presentation

**UFO** (`render_ufo`, DRA-104). The UFO's two hitbox shapes, filled. `obj.hitbox[0]` is the disc box and `obj.hitbox[1]` the dome circle (`ufo_hitbox` builds them in that order); a hitbox that isn't exactly a `Box` then a `Circle` raises `TypeError`. Each shape is drawn with `ui.shapes.draw_shape`, moved to `center` and scaled: the dome as `Circle(center[0] + c.cx × scale, center[1] + c.cy × scale, c.r × scale)` in `dim_color(UFO_DOME_COLOR, brightness)`, (90, 220, 110) at full brightness, first; then the disc as `Box(center[0] + b.cx × scale, center[1] + b.cy × scale, b.w × scale, b.h × scale)` in `dim_color(UFO_DISC_COLOR, brightness)`, (170, 170, 185), on top. So the dome's lower half lies under the disc and the look is a grey saucer with a green dome on top, exactly on the debug outlines. Source: drifters/07-ufo.md, placeholder_look, look_reference, size, hitbox (guess); 07-drifters.md, rule 8.
- Full size at (320, 300): grey on columns 300 to 339, rows 295 to 304, e.g. (320, 300), (300, 296) and (339, 304); green above the disc around x 320, e.g. (320, 290) and (314, 293); background at (320, 284), (299, 300), (340, 300) and (320, 306). During the re-hit cooldown: (128, 128, 139) at (320, 300) and (68, 165, 83) at (320, 290).
- In the entry warning the view draws the UFO itself (the base `warning_copy()`) at the warning's scale, 14 / 40 = 0.35: a grey bar 14 × 3.5 with a green dome of radius 3 on top. No tilt: it flies level.
- No beam, no lights, no spin, no sprite, no sound (scope report DRA-104, Out: final art and sound).
