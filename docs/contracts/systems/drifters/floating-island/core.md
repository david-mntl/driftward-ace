# Drifters, the floating island, core
Part of: drifters
Read when: you change how the floating island behaves (`floating_island.py`).

## Diagram

Floating island (DRA-86). One drifter, parked like the coin, born ACTIVE with no warning. Its hitbox is its shape: boxes, or one convex polygon for the triangle. Offsets from the center, y down, at the file's sizes (320 × 120, `arm` 40; the box 120 × 120). `island_hitbox` builds them:
```
rectangle                          box
+----------------------------+     +----------+
|                            |     |          |
|            (0,0)           |     |  (0,0)   |
+----------------------------+     +----------+
Box(0, 0, 320, 120)                Box(0, 0, 120, 120)

l_shape                            l_shape, invert
+---+                              +----------------------------+
|   |                              |  bar                       |
|   +------------------------+     +---+------------------------+
|   bar                      |     |   |
+----------------------------+     +---+
bar Box(0, 40, 320, 40)            bar Box(0, -40, 320, 40)
upright Box(-140, 0, 40, 120)      upright Box(-140, 0, 40, 120)

t_shape                            t_shape, invert
+----------------------------+                   +---+
|  bar                       |                   |   |
+------------+---+-----------+     +-------------+   +---------+
             |   |                 |  bar                      |
             +---+                 +---------------------------+
bar Box(0, -40, 320, 40)           bar Box(0, 40, 320, 40)
stem Box(0, 0, 40, 120)            stem Box(0, 0, 40, 120)

triangle                           triangle, invert
(-160,-60)                         (-160,-60)          (160,-60)
 |\                                 +-------------------/
 |   \                              |              /
 |       \                          |         /
 |           \                      |    /
 +--------------\ (160,60)          |/
(-160,60)                          (-160,60)
Polygon(((-160,-60), (160,60), (-160,60)))    Polygon(((-160,60), (160,-60), (-160,-60)))
slope's outward normal (120, -320) / 341.76   slope's outward normal (120, 320) / 341.76
  = (0.3511, -0.9363): up and right             = (0.3511, 0.9363): down and right
```
The L's upright and the T's stem are full height, so the two boxes overlap in an `arm` × `arm` square. Their union is the shape drawn. `invert` mirrors the shape top to bottom: every box's `cy` and every polygon point's y is negated (the triangle's point order turns round; collision accepts either order).

Island timeline, rectangle, Level 1, placed with x 320 and no y, added at the end of tick T with the world already scrolling (`scroll_step_px` 1.1 on every later tick). `n` counts ticks after T:
```
state after tick   T        T+1      T+n                T+545     T+546
phase              ACTIVE   ACTIVE   ACTIVE             ACTIVE    dropped
y                  -60.00   -58.90   -60 + n × 1.1      539.50    540.60
hitbox             Box 320 × 120, centered, on every ACTIVE state
has_entered        no       yes      yes                yes
warning            none, ever
```
At T its bottom edge is on the top edge. On T+545 its top edge is at 479.50, still on screen; on T+546 it is at 480.60 and the run drops it. Placed on screen (a `y` given), it shows there at once. At Level 8 it moves 1.87 px a tick, only because the scroll does: hazard speed × and Timer × never touch it.

## Interface

### game/core/drifters/floating_island.py (DRA-86)
```python
# Imports: stdlib, core.collision, core.drifters.base, core.drifters.registry.

class IslandShape(Enum):
    """The shape kinds an island variant can have. drifters/05-floating-islands.md, Shapes."""
    RECTANGLE = "rectangle"   # a filled rectangle; the box variant is one too, 120 x 120
    L_SHAPE = "l_shape"       # a bar along the bottom, an upright at the left end, full height
    T_SHAPE = "t_shape"       # a bar along the top, a stem centered under it, full height
    TRIANGLE = "triangle"     # a right triangle: base along the bottom, straight side on the left

INVERTIBLE_SHAPES: Final[frozenset[IslandShape]] = frozenset(
    {IslandShape.L_SHAPE, IslandShape.T_SHAPE, IslandShape.TRIANGLE}
)  # drifters/05-floating-islands.md, rule 9: invert is for the L, the T and the triangle only

@dataclass(frozen=True, slots=True)
class IslandVariantExtra(VariantExtra):
    """The island's per-variant value: its shape kind."""
    shape: IslandShape

@dataclass(frozen=True, slots=True, kw_only=True)
class IslandTypeExtra(DrifterTypeExtra):
    """The island's values that hold for every variant. Final numbers, px."""
    arm: float                # the L's and the T's arm thickness, px, > 0

def island_hitbox(shape: IslandShape, width: float, height: float, arm: float,
                  invert: bool) -> Hitbox: ...
    # Offsets from the island's center (Diagram, Floating island), with hw = width / 2,
    # hh = height / 2, offset = (height - arm) / 2, and s = -1 with invert, else 1:
    # RECTANGLE: (Box(0, 0, width, height),)
    # L_SHAPE:   (Box(0, s × offset, width, arm), Box(-(width - arm) / 2, 0, arm, height))  bar, upright
    # T_SHAPE:   (Box(0, -s × offset, width, arm), Box(0, 0, arm, height))                  bar, stem
    # TRIANGLE:  (Polygon(((-hw, -s × hh), (hw, s × hh), (-hw, s × hh))),)
    # Every number a float. Pure.

@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class FloatingIsland(Drifter):
    """Forced-path blocker. Sits still in the world and moves down only with the scroll.
    Touching it neither hurts nor pays: it blocks the ship. drifters/05-floating-islands.md."""
    drifter_type: ClassVar[DrifterType] = DrifterType.FLOATING_ISLAND
    parked: ClassVar[bool] = True
    shape: IslandShape = IslandShape.RECTANGLE   # from the variant
    invert: bool = False                         # the placement's invert: the shape upside down
    arm: float = 0.0                             # from the type, px

    @classmethod
    def born(cls, birth: Birth) -> Self: ...          # ACTIVE from birth: no entry warning
    @classmethod
    def start_position(cls, x: float | None, y: float | None, width: float, height: float,
                       invert: bool) -> tuple[float, float]: ...
        # x is required: None raises ValueError("floating_island placement needs x"). y None: -height / 2.
    def update(self, ctx: TickContext) -> Self: ...   # y += ctx.scroll_step_px while ACTIVE
    def effect_on_touch(self) -> TouchEffect: ...     # TouchEffect.BLOCK
```
The fields have defaults so `born_drifter` can build the island before `born` sets them. Sizes and `arm` are whole even px (the schema asks for even integers), so every box edge and every triangle corner falls on a whole px once the center is rounded (Rationale). `app.tuning` imports `IslandShape`, `IslandVariantExtra`, `IslandTypeExtra` and `island_hitbox` to build the tuning records, so the hitbox is worked out in one place. It uses the base `drawn_parts` (the footprint holds the whole look) and the base `collect_points` and `collect_popup`.

## Rules

Floating island (`core/drifters/floating_island.py`, DRA-86). Source: drifters/05-floating-islands.md; scope report DRA-86:
- **Archetype:** Forced-path blocker. A parked drifter: it doesn't move on its own, only down with the scroll. Source: archetype, kind, scroll_kind (locked); rule 3; 03-world-and-camera.md, rule 9.
- **Variants:** `rectangle`, the default, 320 × 120; `box`, 120 × 120; `l_shape`, `t_shape` and `triangle`, each 320 × 120. Every size is the box around the shape, centered on the island's position. A variant is a shape kind (`IslandShape`) and a size; the box is a rectangle kind. The tuning file gives each variant's `shape`, `width` and `height`, and `arm` (40) once for the type; `app.tuning` builds each variant's un-inverted hitbox with `island_hitbox`. Source: variants, default_variant, the Shapes table, arm (guess); scope report DRA-86, Decision log (Q2: "All five, listed sizes").
- **Hitbox:** the shape itself, exactly as drawn (Diagram, Floating island). The rectangle and the box: one box. The L: the bar along the bottom, full width and `arm` tall, and the upright at the left end, `arm` wide and full height. The T: the bar along the top and the stem centered under it, full height. The triangle: one polygon, its base along the bottom, its straight side up the left edge, its slope from the top-left corner to the bottom-right. `island_hitbox` is the one place that rule lives. Source: hitbox (guess); 07-drifters.md, rule 8.
- **Born:** refuses a specialty (`ValueError("floating_island has no specialty")`). Reads `birth.variant_extra`, which must be an `IslandVariantExtra`, else `ValueError("floating_island variant '<name>' has no shape")`, and `birth.type_extra`, which must be an `IslandTypeExtra`, else `ValueError("floating_island tuning has no type values")`. `birth.invert` True on a shape not in `INVERTIBLE_SHAPES` raises `ValueError("floating_island variant '<name>' has no invert")`. Then `replace(born_drifter(cls, birth), phase=Phase.ACTIVE, ticks_in_phase=0, shape=..., invert=birth.invert, arm=type_extra.arm, hitbox=island_hitbox(shape, birth.width, birth.height, arm, birth.invert))`. Its `speed` is the spawner's 0.0 and its `warning_ticks` the file's 0. Source: entry_warning (locked: none); rule 9 (`invert` for the L, the T and the triangle only); specialty (locked: none).
- **No warning of any kind.** It is ACTIVE on the state it is added, so nothing is drawn for it before the island itself scrolls in. No telegraph. Source: entry_warning, telegraph (locked); rules 1 and 2; scope report DRA-86, Feature ("with no warning of any kind").
- **Start:** `start_position`: x is the placement's (required: `ValueError("floating_island placement needs x")` without it). y is the placement's, or `-height / 2` (−60 at 120 tall) when None: its bottom edge on the top edge, fully off screen. Source: enters_from (locked); rule 1; 07-drifters.md, rules 13 and 14.
- **Update:** in ACTIVE, `y += ctx.scroll_step_px` and `ticks_in_phase + 1`; `x` never changes. In WARNING and GONE, unchanged. The ship in `ctx` is never read. Before the scroll starts it stands still; then it moves exactly as the starfield and the coins do. Source: rule 3.
- **Touch:** `effect_on_touch()` is BLOCK. Touching it never hits and never pays, invulnerable or not: no `drifter touch` line, no life, no cooldown, no points (The base, Block). It blocks the ship (`systems/ship.md`, Islands), in the respawn wait too, and moves the fall respawn spot (`systems/run.md`, step 6). Source: rules 4 to 6; 05-lives-and-damage.md, rule 2.3.
- **Drawn parts:** the base footprint, `Box(x, y, width, height)`: the look is the union of its shapes, which fills at most that box. Source: 07-drifters.md, rule 12.
- **Leaving:** the base rule on that box. It starts fully above the top edge, so it is never removed before it has entered; once it has, it is removed when its top edge is at or below the floor (y ≥ 540 at 120 tall). Placed on screen near a side, it is never fully past a side, as it never moves sideways. Source: rule 7; 07-drifters.md, rule 12.
- **Scales:** nothing. Its size and shape never change with level; `as_level` is accepted and changes nothing. Source: rule 8.
- It accepts `x`, `y`, `variant`, `invert` (L, T, triangle) and `as_level`. A specialty and `speed` are refused (the spawner's parked rule: `floating_island has no speed`). Drifters pass through it with no effect: only the ship collides with it. Source: rule 9; 07-drifters.md, rules 13 and 15.
- **For wave_check** (built in `tools/wave_check/` outside this contract's tasks; 09-waves.md, rule 7). An island is told apart by its type, `drifter_type is DrifterType.FLOATING_ISLAND` (a track's kind `"floating_island"`), or by `effect_on_touch() is TouchEffect.BLOCK`, which every blocker shares. For check 7, a coin sits inside an island on a tick where both are ACTIVE and `hitboxes_overlap(coin.current_hitbox(), island.current_hitbox())` is True: the strict test, the triangle's polygon included, so a coin touching an island's edge from outside passes and any shared area fails. Both are parked, so once both are on the field their places relative to each other never change, and one tick with both present decides it. For the coin-near check, an island's `grow_hitbox` is exact for its polygon too. The bot's island physics is `core.ship.step(ship, thrust, ground)` with the ground `core.run.island_ground` builds (`systems/run.md`). Source: 09-waves.md, rule 7.7 and the hazard note under rule 7; scope report DRA-86, Limits (wave_check).
