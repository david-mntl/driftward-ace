# Drifters, the satellite, core
Part of: drifters
Read when: you change how the satellite behaves (`satellite.py`).

## Diagram

Satellite timeline, flat, Level 1, placed at y 300 with no x and no `invert`, added at the end of tick T:
```
state after tick   T        T+1..T+59   T+60        T+61            ...  T+60+n
phase              WARNING  WARNING     ACTIVE      ACTIVE               ACTIVE
x                  -18.00   -18.00      -18.00      -15.5325             -18 + n × 2.4675
y                  300.00   300.00      300.00      300.00               300.00
hitbox             none     none        two boxes   two boxes
has_entered        no       no          no          yes                  yes
warning shows at   (18, 300)
```
At T+60 its right edge is on the left wall: it touches the screen but is not on it. Without the entered rule it would be dropped right there. Dropped on the first state where its left edge is at or past x 640: x − 18 ≥ 640, so n = 274 (x ≈ 658.10, about 4.6 s after it appears).

Angled at Level 1: `velocity_x` = 2.4675 × cos 20° ≈ 2.3187, `velocity_y` = 2.4675 × sin 20° ≈ 0.8439. Placed at y 200 from the left wall, it is dropped past the right wall on n = 292 (x ≈ 659.06, y ≈ 446.43). Placed at y 300, it is dropped below the floor first, on n = 221 (x ≈ 494.43, y ≈ 486.51, top edge ≈ 480.51). With `invert` it starts at x 658 and `velocity_x` is negative.

## Interface

### game/core/drifters/satellite.py (DRA-39)
```python
# Imports: stdlib (math), core.world, core.drifters.base, core.drifters.registry.
@dataclass(frozen=True, slots=True)
class SatelliteVariantExtra(VariantExtra):
    """The satellite's own per-variant value."""

    angle_degrees: (
        float  # path angle below level, degrees, 0 <= angle < 90. 0 flat, 20 angled
    )


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Satellite(Drifter):
    """Side crosser. Crosses from a side wall in a straight line. drifters/02-satellite.md."""

    drifter_type: ClassVar[DrifterType] = DrifterType.SATELLITE
    invert: bool = False  # True: enters from the right wall and flies right to left
    angle_degrees: float = 0.0  # path angle below level, degrees, from the variant
    velocity_x: float = 0.0  # px/tick, + is right. Final, set at birth
    velocity_y: float = 0.0  # px/tick, + is down. Final, set at birth

    @classmethod
    def born(cls, birth: Birth) -> Self: ...
    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        ...
        # y is required: None raises ValueError("satellite placement needs y").
        # x None: -width / 2, or SCREEN_W + width / 2 with invert.

    def update(self, ctx: TickContext) -> Self: ...
    def effect_on_touch(self) -> TouchEffect: ...  # TouchEffect.HIT
    def warning_tilt_degrees(
        self,
    ) -> float: ...  # -angle_degrees, or +angle_degrees with invert
```
The fields have defaults so `born_drifter` can build the satellite before `born` sets them.

## Rules

Satellite (`core/drifters/satellite.py`, DRA-39). Source: drifters/02-satellite.md:
- **Archetype:** Side crosser. A moving drifter: its speed is its on-screen speed along its path, and the scroll doesn't add to it. Source: archetype, kind (locked); rule 3; 03-world-and-camera.md, rule 9.
- **Variants:** `flat`, the default, at 0° from level, and `angled`, at 20° below level. Both 36 × 12 with the same two-box hitbox: the body, a 12 × 12 box, and the panel bar, a 36 × 6 box, both centered. The angle comes from the tuning file (`SatelliteVariantExtra.angle_degrees`). Source: variants, default_variant, size, hitbox (guess); 07-drifters.md, rule 10.
- **Start:** `start_position`: y is the placement's (required: `ValueError("satellite placement needs y")` without it; the spec gives no default y). x is the placement's, or when None just outside the wall it enters from, touching it: `-width / 2` (x −18) by default, `SCREEN_W + width / 2` (x 658) with `invert`. Source: start, rule 7 (placing: y, variant, invert) (guess); 07-drifters.md, rule 14.
- **Born:** refuses a specialty (`ValueError("satellite has no specialty")`). Reads `birth.variant_extra`, which must be a `SatelliteVariantExtra`, else `ValueError("satellite variant '<name>' has no angle")`. Then `replace(born_drifter(cls, birth), invert=birth.invert, angle_degrees=angle, velocity_x=..., velocity_y=...)` with `velocity_x = speed × cos(angle)`, negated with `invert`, and `velocity_y = speed × sin(angle)`, the angle in radians from `angle_degrees`. Final numbers: set once, at birth. Source: rules 3 and 6 (the angle never scales); specialty (locked).
- **Update:** in WARNING, `tick_warning(self)`. In ACTIVE, `x += velocity_x`, `y += velocity_y` and `ticks_in_phase + 1`. In GONE, unchanged. No targeting, no turning; the ship in `ctx` is never read. Flat: level, `velocity_y` 0. Angled: 20° below level. Away from the wall it entered from: right without `invert`, left with it. Source: rule 3; direction (guess).
- **Touch:** `effect_on_touch()` is HIT: touching the body or the panel bar is a hit. Graze zone: both boxes grown by 14. Source: rule 4; graze (locked).
- **Hitting again:** the shared re-hit cooldown. Source: Edge cases; 05-lives-and-damage.md, rule 1.5.
- **Warning:** at its y against the wall it enters from (`warning_center`: x 18, or 622 with `invert`). `warning_tilt_degrees()` is `-angle_degrees` without `invert` and `+angle_degrees` with it: the angled copy turns 20° clockwise when it will fly down to the right, counterclockwise when down to the left. Flat: 0. Source: rule 1.
- **Leaving:** the base rule. It starts fully off screen, so it is never removed before it has entered; once it has, it is removed fully past a side wall or fully below the floor. It flies through the walls and through other drifters. Source: rule 5; 07-drifters.md, rules 12 and 15.
- **No telegraph, no specialty.** Source: telegraph, specialty (locked); rule 2.
- **Speed at Level 1:** `0.375 × TOP_SIDE_SPEED` ≈ 2.4675 px/tick along its path, its own `speed_ratio`. Angled: ≈ 2.3187 across and ≈ 0.8439 down per tick. Source: speed_ratio, speed (guess, derived).
- A flat satellite placed above the top line can never reach the ship. Allowed. Source: Edge cases.
