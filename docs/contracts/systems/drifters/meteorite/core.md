# Drifters, the meteorite, core
Part of: drifters
Read when: you change how the meteorite behaves (`meteorite.py`).

## Diagram

Meteorite timeline, medium, Level 1, added at the end of tick T:
```
state after tick   T        T+1..T+59   T+60            T+61          ...  T+60+n
phase              WARNING  WARNING     ACTIVE          ACTIVE             ACTIVE
ticks_in_phase     0        1..59       0               1                  n
y                  -14.00   -14.00      -14.00          -14 + 2.4675       -14 + n × 2.4675
hitbox             none     none        circle r 14     circle r 14
has_entered        no       no          no              yes                yes
```
At T+60 its bottom edge is on the top edge, so it is not yet on the screen. Dropped on the first state where its top edge is at or past y 480: y − 14 ≥ 480, so n = 206 (y ≈ 494.3).

## Interface

### game/core/drifters/meteorite.py
```python
# Imports: stdlib, core.drifters.base, core.drifters.registry.
@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Meteorite(Drifter):
    """Falling blocker. Falls straight down at its speed. drifters/01-meteorite.md."""

    drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        ...
        # x is required: None raises ValueError("meteorite placement needs x"). y None: -height / 2.

    def update(self, ctx: TickContext) -> Self: ...
    def effect_on_touch(self) -> TouchEffect: ...  # TouchEffect.HIT
```
No new fields. It uses the base `born` (so `invert` True raises) and the base `may_hit_ship`. DRA-39 removes its `default_y` and its own `may_hit_ship` (the "hits once" stand-in).

## Rules

Meteorite (`core/drifters/meteorite.py`). Source: drifters/01-meteorite.md:
- **Archetype:** Falling blocker. A moving drifter: its speed is its on-screen speed and the scroll doesn't add to it. Source: archetype, kind (locked); 03-world-and-camera.md, rule 9.
- **Start:** `start_position`: x is the placement's (required: `ValueError("meteorite placement needs x")` without it); y is the placement's, or `-height / 2` when None: its bottom edge on the top edge. The variants are round, so height = width and this is the spec's `−width ÷ 2`. Source: start_y (guess); rule 1.
- **Update:** in WARNING, `tick_warning(self)`. In ACTIVE, `y += speed` and `ticks_in_phase + 1`; `x` never changes. In GONE, unchanged. No drift, no spin, no targeting. Source: rule 3.
- **Touch:** `effect_on_touch()` is HIT. Source: rule 4.
- **Hitting again:** the shared re-hit cooldown (The base, above). A meteorite that hit the ship stays, keeps falling, and can hit again once its cooldown ends. Source: Edge cases; 05-lives-and-damage.md, rule 1.5.
- **No specialty, no telegraph, no invert.** The entry warning is its only warning. A placement with `invert` True raises (base `born`). Source: specialty, telegraph (locked); rules 2 and 7 (placing names x, y and variant only).
- **Speed at Level 1:** `0.375 × TOP_SIDE_SPEED` = 0.375 × 6.58 ≈ 2.4675 px/tick with the current ship guesses. At Level 8: × 1.42 ≈ 3.50. Source: speed_ratio, speed (guess, derived); 91-decision-log.md, row 40.
