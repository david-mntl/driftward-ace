# Drifters, the electric ball, view
Part of: drifters
Read when: you change how the electric ball looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/electric_ball_view.py (new, DRA-111). Imports: pygame, math, core.drifters.base,
# core.drifters.electric_ball, ui.drifters.registry. Never app.
ELECTRIC_BALL_COLOR: Final[tuple[int, int, int]]    # drifters/10-electric-ball.md, placeholder_look, ball (guess)
ELECTRIC_CHARGE_COLOR: Final[tuple[int, int, int]]  # same, the charge's rays and outline
ELECTRIC_FILL_COLOR: Final[tuple[int, int, int]]    # same, the firing circle's fill
ELECTRIC_RIM_COLOR: Final[tuple[int, int, int]]     # same, the firing circle's rim
FIRST_RAY_DEGREES: Final[float]                     # drifters/03-chain-lightning.md, ray_length: the first
                                                    # ray on the first diagonal it names (reused, scope report
                                                    # DRA-111, Left to the Architect). Counterclockwise on
                                                    # screen from pointing right

@register_view(DrifterType.ELECTRIC_BALL)
def render_electric_ball(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
                         scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_electric_ball draws an ElectricBall") for any other drifter.
```
The module keeps one dict of pre-rendered firing-circle images (Presentation, Fill and rim). `game/ui/drifters/__init__.py` gains one import line, `electric_ball_view`, in sorted order (between `coin_view` and `fireball_view`); ruff's import-sort rule enforces it.

## Presentation

**Electric ball** (`render_electric_ball`, DRA-111). Any drifter that is not an `ElectricBall` raises `TypeError`. Every fact it shows is a core field or method; it never works out the cycle, whether the ball is on screen, or what fires.

| Core field or method | Shown as |
|---|---|
| `obj.width` | the ball: a filled circle `obj.width` across |
| `obj.pulse_fires()`, `obj.pulse_radius`, `obj.fill_opacity`, `obj.rim_width` | the firing circle: filled, translucent, with its bright rim, only while `pulse_fires()` |
| `obj.outline_level()`, `obj.pulse_radius`, `obj.outline_width` | the charge outline of the pulse circle, at that share of full color; not drawn at 0 |
| `obj.charge_ray_count()`, `obj.charge_rays`, `obj.ray_length`, `obj.ray_width` | how many rays show now, how they are spread, how long and how thick |
| `obj.brightness()` | through the `brightness` argument: every part dims together during the re-hit cooldown |

Drawn in this order, every color through `dim_color`, every position at `center` and every size × `scale`, with `cx, cy = round(center[0]), round(center[1])`:
1. **Fill and rim**, only while `obj.pulse_fires()`. One image, blitted centered on `(cx, cy)`: with `r = round(obj.pulse_radius × scale)`, a `pygame.SRCALPHA` surface of side `2 × r + 1`, a filled circle of radius `r` on its middle pixel in `dim_color(ELECTRIC_FILL_COLOR, brightness)` at alpha `round(255 × obj.fill_opacity)`, then a ring of width `max(1, round(obj.rim_width × scale))` on the same circle, opaque, in `dim_color(ELECTRIC_RIM_COLOR, brightness)`. pygame draws a ring's width inward, so the rim lies inside the circle and the whole firing look covers exactly the hitbox circle. Source: placeholder_look (Fire); rule 9 ("The firing look stays inside the pulse circle, so the hitbox is never bigger than what the player sees").
2. **Charge outline**, only while `obj.outline_level() > 0`: `pygame.draw.circle(surface, dim_color(ELECTRIC_CHARGE_COLOR, brightness × obj.outline_level()), (cx, cy), round(obj.pulse_radius × scale), max(1, round(obj.outline_width × scale)))`. Faint with the first ray, at full color once every ray shows. It shows exactly where the strike will land. Source: telegraph (locked); placeholder_look (Charge).
3. **Ball**, always: a filled circle in `dim_color(ELECTRIC_BALL_COLOR, brightness)`, center `(cx, cy)`, radius `round(obj.width × scale / 2)`. On top of the fill, so the ball reads while it fires. Source: placeholder_look (ball); ball_size.
4. **Rays**, `obj.charge_ray_count()` of them (0 unless it charges with the ball on screen). Ray `k` (from 0) points at `FIRST_RAY_DEGREES + k × 360 / obj.charge_rays` degrees, counterclockwise on screen from pointing right: direction `(cos θ, −sin θ)`. It runs from `ball + direction × obj.width / 2 × scale` (the ball's edge) to `ball + direction × (obj.width / 2 + obj.ray_length) × scale`, drawn with `pygame.draw.line(surface, dim_color(ELECTRIC_CHARGE_COLOR, brightness), start, end, max(1, round(obj.ray_width × scale)))`. The chain lightning's ray rule, around one ball. Source: telegraph; drifters/03-chain-lightning.md, charge_rays and ray_length; placeholder_look (Charge).

**Fill and rim pre-rendered.** The firing-circle image is built once per key `(r, rim px, alpha, fill color, rim color)` after dimming, kept in the module's dict and blitted each frame; never rebuilt per frame. The keys are few: one radius per variant and two brightness values. Source: 12-art-and-audio.md, rule 3 (glow is pre-rendered); 15-tech-constraints.md, rule 5.

**In the entry warning** the view draws the electric ball itself (the base `warning_copy()`) at the warning's scale, `ENTRY_WARNING_COPY_SIZE / obj.width`: in WARNING it neither charges nor fires, so the copy is the purple ball alone. No tilt. Source: 07-drifters.md, entry_warning_look and entry_warning_size.

**Brightness.** Every part dims together during the re-hit cooldown: the view gets `obj.brightness()` and multiplies each color by it through `dim_color`; the outline multiplies it by `outline_level()` too. Source: 05-lives-and-damage.md, rule 1.5, rehit_dim.

No art, no glow, no flicker, no jagged lightning, no sound (scope report DRA-111, Out: final art and sound). The "faster" of the GDD's telegraph is left to the real look; the placeholder shows the growing count, as the chain lightning does.
