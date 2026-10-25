# Drifters, the planet, core
Part of: drifters
Read when: you change how the planet behaves (`planet.py`).

## Diagram

Planet (DRA-96). One drifter: a body, its hitbox circle, and around it a gravity field drawn as rings. Parked like the coin, but a hazard: born in WARNING with the shared entry warning. At the file's values (size 64, `pull_radius` 150, `pull_max` 0.2), offsets from the center, y down:
```
                 . - ~ ~ ~ - .            outer ring: 1 px at pull_radius (150), always on
             . '    . - - .    ' .        inner rings: 1 px, sliding from 150 in to the surface,
           .      '         '      .                   fading 50% -> 0%
          .      .   .---.   .      .
          .      .  ( (0,0) ) .      .    body: filled circle r 32 = Circle(0, 0, 32), the hitbox
          .      .   '---'   .      .     graze zone: Circle(0, 0, 46)
           .      .         .      .
             ' .    ' - - '    . '        drawn parts: Box(0, 0, 302, 302): the field ring's
                 ' - ~ ~ ~ - '                         150 + FIELD_DRAW_MARGIN 1 on each side
pull: 0 at d >= 150, 0.2 × (150 - d) / 118 between, 0.2 at d <= 32 (systems/ship.md, Planet pull)
```

Planet timeline, standard, Level 1, placed with x 320 and no y, added at the end of tick T with the world already scrolling (`scroll_step_px` 1.1 on every later tick). `n` counts ACTIVE ticks:
```
state after tick   T        T+1..T+59   T+60       T+61      T+60+n             T+770     T+771
phase              WARNING  WARNING     ACTIVE     ACTIVE    ACTIVE             ACTIVE    dropped
ticks_in_phase     0        1..59       0          1         n                  710
y                  -151.00  -151.00     -151.00    -149.90   -151 + n × 1.1     630.00    631.10
hitbox             none     none        circle r 32 on every ACTIVE state
gravity_well()     None     None        (320, y), surface 32, pull radius 150, pull max 0.2
has_entered        no       no          no         yes       yes                yes
warning shows at   (320, 12)
```
At T+60 the drawn box's bottom edge is on the top edge (y −151 + 151 = 0): nothing drawn is on screen, the field ring's lowest pixel row is above it, and the field already pulls. On T+770 the box's top edge is at 479.00, still on screen; on T+771 it is at 480.10 and the run drops it, the field with it. A ship standing still at (320, 240) is inside the field from T+280 (y 91.00, 149 px away) and touched by the body from T+372 (y 192.20: the circle reaches 224.20, past the bar's top edge at 224). At Level 8 it moves 1.87 px a tick, only because the scroll does.

Inner field rings, `inner_rings()`, at the file's values (`field_ring_trip` 120, `field_ring_gap` 60, `field_ring_fade` 50, `field_ring_count` 2). `t` is `ticks_in_phase` while ACTIVE; ring `i` (from 0) is `k = (t − i × 60) mod 120` ticks into its trip:
```
t      ring 0: k   radius    opacity      ring 1: k   radius    opacity
0          0       150.00    0.5000           60       91.00     0.2500
30         30      120.50    0.3750           90       61.50     0.1250
60         60      91.00     0.2500           0        150.00    0.5000
119        119     32.98     0.0042           59       91.98     0.2542
120        0       150.00    0.5000           60       91.00     0.2500     the cycle repeats
radius = 150 − 118 × k / 120;  opacity = 0.5 × (1 − k / 120)
```

## Interface

### game/core/drifters/planet.py (DRA-96)
```python
# Imports: stdlib, core.collision, core.ship (GravityWell), core.drifters.base,
# core.drifters.registry.

FIELD_DRAW_MARGIN: Final[float] = 1.0   # px the field ring's drawn pixels may reach past
                                        # pull_radius. Not a game value (Rationale)

@dataclass(frozen=True, slots=True)
class PlanetVariantExtra(VariantExtra):
    """The planet's per-variant values: its gravity field."""
    pull_radius: float        # px from the center where the pull is 0: the field's edge,
                              # > the planet's radius
    pull_max: float           # px/tick², the pull at the surface, > 0

@dataclass(frozen=True, slots=True, kw_only=True)
class PlanetTypeExtra(DrifterTypeExtra):
    """The planet's values that hold for every variant: the inner field rings' look."""
    field_ring_trip: int      # ticks an inner ring takes from pull_radius to the surface, >= 1
    field_ring_gap: int       # ticks each inner ring runs behind the one before it, >= 0
    field_ring_fade: float    # % opacity of an inner ring at pull_radius, 0 to 100; 0 at the surface
    field_ring_count: int     # how many inner rings, >= 0

@dataclass(frozen=True, slots=True)
class FieldRing:
    """One inner field ring on this state. A look only: it never changes the pull."""
    radius: float             # px from the planet's center, surface < radius <= pull_radius
    opacity: float            # 0..1, of the ring color

def planet_hitbox(size: float) -> Hitbox: ...
    # (Circle(0.0, 0.0, size / 2),): the planet's circle, centered. Pure.

@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Planet(Drifter):
    """Gravity well. Sits still in the world and moves down only with the scroll. Inside its
    field it pulls the ship toward its center. Touching it is a hit. drifters/08-planet.md."""
    drifter_type: ClassVar[DrifterType] = DrifterType.PLANET
    parked: ClassVar[bool] = True
    pull_radius: float = 0.0          # from the variant, px
    pull_max: float = 0.0             # from the variant, px/tick²
    field_ring_trip: int = 1          # from the type, and every value below
    field_ring_gap: int = 0
    field_ring_fade: float = 0.0
    field_ring_count: int = 0

    @classmethod
    def born(cls, birth: Birth) -> Self: ...          # in WARNING, like every hazard
    @classmethod
    def start_size(cls, width: float, height: float,
                   variant_extra: VariantExtra | None) -> tuple[float, float]: ...
        # With a PlanetVariantExtra: both 2 × (pull_radius + FIELD_DRAW_MARGIN), the field
        # ring's box. Otherwise (width, height): born refuses that tuning right after.
    @classmethod
    def start_position(cls, x: float | None, y: float | None, width: float, height: float,
                       invert: bool) -> tuple[float, float]: ...
        # x is required: None raises ValueError("planet placement needs x"). y None: -height / 2.
    def update(self, ctx: TickContext) -> Self: ...   # WARNING: tick_warning. ACTIVE:
                                                      # y += ctx.scroll_step_px. GONE: unchanged
    def effect_on_touch(self) -> TouchEffect: ...     # TouchEffect.HIT
    def surface_radius(self) -> float: ...            # width / 2, px: the body's radius
    def drawn_parts(self) -> tuple[Box, ...]: ...     # (Box(x, y, s, s),), s = 2 × (pull_radius
                                                      # + FIELD_DRAW_MARGIN): the field ring's box
    def gravity_well(self) -> GravityWell | None: ... # ACTIVE: GravityWell(x, y,
                                                      # surface_radius(), pull_radius, pull_max).
                                                      # WARNING and GONE: None
    def inner_rings(self) -> tuple[FieldRing, ...]: ...  # ACTIVE: field_ring_count rings
                                                      # (Rules, Planet, Field rings). Else ()
```
The fields have defaults so `born_drifter` can build the planet before `born` sets them. `app.tuning` imports `PlanetVariantExtra`, `PlanetTypeExtra` and `planet_hitbox` to build the tuning records, so the hitbox is worked out in one place. It uses the base `warning_center`, `warning_tilt_degrees`, `warning_copy`, `settle_warning`, `graze_zone`, `collect_points` and `collect_popup`.

## Rules

Planet (`core/drifters/planet.py`, DRA-96). Source: drifters/08-planet.md; scope report DRA-96:
- **Archetype:** Gravity well. A parked hazard: it doesn't move on its own, only down with the scroll. Source: archetype, kind (locked); rule 3; 03-world-and-camera.md, rule 9.
- **One drifter.** Its body and its field are one drifter. `x`, `y` is the planet's center, the field's too. `width` and `height` are its size, 64: the body. The field reaches past them (Drawn parts, below). Source: size; rule 1.
- **Variants:** one, `standard`, the default: size 64, `pull_radius` 150, `pull_max` 0.2. Size and pull are per variant: a new size or pull is a new variant, a new entry in the tuning file with no code. Looks are not variants: one placeholder look, picked every time, so `look_pick` holds; the skin list waits for the art (scope report DRA-96, Out). Source: variants, default_variant, size, pull_radius, pull_max (guess); look_pick (locked); How to extend.
- **Hitbox:** one circle, radius size ÷ 2 (32), centered: `planet_hitbox(64)`, `Circle(0, 0, 32)`. Only the body. Graze zone (base): the circle grown by the drifter's `graze_margin`; the run's graze step pays for it (`systems/run.md`, step 5b). The field never grazes. Source: hitbox (guess); graze (locked); 07-drifters.md, rule 8; 06-scoring.md, rules 3 and 4.
- **Born:** refuses a specialty (`ValueError("planet has no specialty")`) and an invert (`ValueError("planet has no invert")`), as the base does. Reads `birth.variant_extra`, which must be a `PlanetVariantExtra`, else `ValueError("planet variant '<name>' has no pull")`, and `birth.type_extra`, which must be a `PlanetTypeExtra`, else `ValueError("planet tuning has no type values")`. Then `replace(born_drifter(cls, birth), pull_radius=..., pull_max=..., field_ring_trip=..., field_ring_gap=..., field_ring_fade=..., field_ring_count=...)`, from the variant and the type. It stays in WARNING with `ticks_in_phase` 0, as every hazard. Its `speed` is the spawner's 0.0 (parked) and its `warning_ticks` the file's 60. Source: specialty (locked: none); rule 9 (no invert); entry_warning_ticks (07-drifters.md, the shared value).
- **Warning:** the shared entry warning, `entry_warning_ticks` long, from the base: at its x against the top edge for a top start (`warning_center()` (x, 12), x kept 12 px inside each side); at its placed spot when that is on screen. The copy is the planet itself, drawn as its body only at the copy's scale (Presentation, Planet). It doesn't move while the warning shows, and turns ACTIVE where it was placed. No telegraph. Source: rules 1 and 2; telegraph (locked: none); 07-drifters.md, rule 9.
- **Start:** `start_size` gives `2 × (pull_radius + FIELD_DRAW_MARGIN)` for both: 302 × 302, the field ring's box. `start_position`: x is the placement's (required: `ValueError("planet placement needs x")` without it). y is the placement's, or `-height / 2` of that box when None: −151, so the field ring's box touches the top edge from above and nothing drawn is on screen. Source: enters_from (locked); rule 1; 07-drifters.md, rules 12 and 14; scope report DRA-96, Limits ("The planet starts with its ring touching the top edge (center 151 px above it)") and Decision log (Q1).
- **Update:** in WARNING, `tick_warning(self)`: it stays where it is. In ACTIVE, `y += ctx.scroll_step_px` and `ticks_in_phase + 1`; `x` never changes. In GONE, unchanged. The ship in `ctx` is never read. Before the scroll starts it stands still; then it moves exactly as the starfield does. Source: rule 3; kind (locked).
- **Touch:** `effect_on_touch()` is HIT: touching the body is a hit, through the run's shared hit rules and the shared re-hit cooldown (body and field dim together). The field never hits. Source: rule 6; Edge cases; 05-lives-and-damage.md, rules 1.5 and 2.7.
- **Field:** `gravity_well()` while ACTIVE is `GravityWell(x=x, y=y, surface_radius=surface_radius(), pull_radius=pull_radius, pull_max=pull_max)`: (x, y), 32, 150, 0.2 at the file's values. In WARNING and GONE it is None. So the field is on from the tick the planet appears and goes with it when it is dropped. How the ship is pulled is the ship's rule (`systems/ship.md`, Planet pull); when it is pulled is the run's (`systems/run.md`, step 4). The pull never changes with level. Source: rules 1, 4, 7 and 8; pull_shape (locked).
- **Field rings:** `inner_rings()` while ACTIVE returns `field_ring_count` rings, ring `i` from 0: `k = (ticks_in_phase − i × field_ring_gap) % field_ring_trip` (Python's `%`, never negative), `progress = k / field_ring_trip`, `radius = pull_radius − (pull_radius − surface_radius()) × progress`, `opacity = field_ring_fade / 100 × (1 − progress)`. So each ring slides at a steady speed from `pull_radius` to the surface in `field_ring_trip` ticks and starts again at `pull_radius`; each runs `field_ring_gap` ticks behind the one before it; each fades in a straight line from `field_ring_fade` % at `pull_radius` to 0 at the surface. Every ring is on its cycle from the first ACTIVE state (with the file's values the second starts halfway in), so the field looks the same whenever it is seen. In WARNING and GONE it is `()`. The rings are looks only: they show where the field is, not how strong the pull is, and never scale with level. Source: field_ring_trip, field_ring_gap, field_ring_fade (guess); placeholder_look ("two faint 1 px rings"); rules 2 ("always drawn"), 8 and 10; 91-decision-log.md, row 76; scope report DRA-96, Decision log (Q2: Director "Figure it out. Make it reasonable.", then "Approve as proposed").
- **Drawn parts:** `drawn_parts()` is `(Box(x, y, s, s),)` with `s = 2 × (pull_radius + FIELD_DRAW_MARGIN)`: 302 × 302, centered on the planet. It holds the outer ring, every inner ring and the body. Source: 07-drifters.md, rule 12 ("every part counts"); scope report DRA-96, Limits and Decision log (Q1).
- **Leaving:** the base rule on that box. It starts with the box fully above the top edge, so it is never removed before it has entered. Once it has, it is removed when the box's top edge is at or below the floor (y ≥ 631 at the file's values): the field ring is fully below the floor, and the planet pulls until then. Placed on screen near a side, it is never fully past a side, as it never moves sideways; it leaves at the floor. Source: rule 7; 07-drifters.md, rule 12.
- **Scales:** nothing. Its size, pull, field, rings and movement never change with level; `as_level` is accepted and changes nothing. A faster scroll only brings it sooner. Source: rule 8.
- It accepts `x`, `y`, `variant` and `as_level`. `invert`, a specialty and `speed` are refused (the spawner's parked rule: `planet has no speed`). Drifters pass through it and its field pulls none of them. Source: rule 9; 07-drifters.md, rules 13 and 15; rule 4.
- **For wave_check** (built in `tools/wave_check/` by the main session after QA, outside this contract's tasks; 09-waves.md, rule 7). A planet is told apart by its type, `drifter_type is DrifterType.PLANET` (a track's kind `"planet"`). It is a hazard for the seam, placement and coin-near checks, measured from its body (`current_hitbox()`, `graze_zone()`), never from its field or its `drawn_parts()`. The bot's pull physics is part 2 of wave_check, not built: when it is, it steps the ship with `core.ship.step(ship, thrust, ground, core.run.gravity_wells(drifters))`. Source: drifters/08-planet.md, rule 11; scope report DRA-96, Limits and Out.
