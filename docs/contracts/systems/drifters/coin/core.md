# Drifters, the coin, core
Part of: drifters
Read when: you change how the coin behaves (`coin.py`).

## Diagram

Coin (DRA-62). One drifter: a crystal 12 × 20, its 12 × 10 middle the hitbox, a ring 22 × 8 across its middle. Parked: it moves only by `ctx.scroll_step_px`. No entry warning: born ACTIVE. Full size, center (x, y), pixel columns and rows as the view draws them at `(cx, cy) = (round(x), round(y))`:
```
column        cx-6 . . . . cx-1 cx . . . . cx+5
row cy-10     .  .  .  .  .  #   #  .  .  .  .  .     top point, 2 px wide
row cy-9      .  .  .  .  #  l   s  #  .  .  .  .
row cy-8      .  .  .  #  l  l   s  s  #  .  .  .
row cy-7      .  .  #  G  G  l   s  s  s  #  .  .     G: the rare glint, 2 x 2, its top-left at (3, 3) in the 12 x 20 box
row cy-6      .  #  l  G  G  l   s  s  s  s  #  .
row cy-5      #  l  l  l  l  l   s  s  s  s  s  #     body top row: the hitbox's top
  ...         (rows cy-4 to cy+3 the same: the ring crosses here)
row cy+4      #  l  l  l  l  l   s  s  s  s  s  #     body bottom row: the hitbox's bottom
row cy+5      .  #  l  l  l  l   s  s  s  s  #  .
  ...
row cy+9      .  .  .  .  .  #   #  .  .  .  .  .     bottom point
l: lit side, s: shade side, #: the 1 px rim. Common coins have no G (lit there).
The ring: a 1 px ellipse in the 22 x 8 rect from (cx-11, cy-4), columns cx-11..cx+10, rows cy-4..cy+3, drawn over the crystal.
```
Drawn parts: the crystal's box `Box(x, y, 12, 20)` and the ring's box `Box(x, y, 22, 8)`. Every drawn pixel lies inside them once moved by the center's rounding, which is at most 0.5 px; the sizes are even whole numbers, so the box edges and the pixel edges both fall on whole px (Rationale).

Coin timeline, common, Level 1, placed with x 320 and no y, added at the end of tick T, with the world already scrolling (T ≥ 30), so `scroll_step_px` is 1.1 on every later tick. `n` counts ticks after T:
```
state after tick   T        T+1      T+9      T+n                T+454     T+455
phase              ACTIVE   ACTIVE   ACTIVE   ACTIVE             ACTIVE    dropped
y                  -10.00   -8.90    -0.10    -10 + n × 1.1      489.40    490.50
hitbox             box 12 × 10, centered, on every ACTIVE state
has_entered        no       yes      yes      yes                yes
warning            none, ever
```
At T its crystal's bottom edge is on the top edge: on no state is a pixel of it drawn before T+1. On T+454 the crystal's top edge is at 479.40, still on screen; on T+455 it is at 480.50 and the ring's at 486.50: every part is off, so the run drops it. Placed on tick 1, before the scroll starts, it stays at y −10 on the states after ticks 1 to 30 and first moves on tick 31. Placed at (440, 210): it is on screen at once, enters on its first update, and is dropped on n = 255 (y 490.50). At Level 8 it moves exactly the same: hazard speed × and Timer × never touch it.

## Interface

### game/core/drifters/coin.py (DRA-62)
```python
# Imports: stdlib, core.collision, core.popup, core.drifters.base, core.drifters.registry.

@dataclass(frozen=True, slots=True)
class CoinVariantExtra(VariantExtra):
    """The coin's per-variant values."""
    points: int               # points paid when collected, >= 1. 50 common, 100 rare
    glint: bool               # True: the view draws the glint. The rare one

@dataclass(frozen=True, slots=True, kw_only=True)
class CoinTypeExtra(DrifterTypeExtra):
    """The coin's values that hold for every variant. Final numbers, px and ticks."""
    body_height: int          # the crystal's middle rectangle, px, even, < the crystal's height.
                              # The hitbox's height
    ring_width: int           # the ring's ellipse, px, even
    ring_height: int          # px, even
    glint_size: int           # the glint's side, px, >= 1
    glint_left: int           # the glint's left edge, px from the crystal box's left edge
    glint_top: int            # the glint's top edge, px from the crystal box's top edge
    popup_ticks: int          # how long the points popup shows, ticks, >= 1
    popup_rise_per_tick: float  # how far the popup rises each tick, px, >= 0

def coin_hitbox(crystal_width: float, body_height: float) -> Hitbox: ...
    # (Box(0.0, 0.0, crystal_width, body_height),): the crystal's middle rectangle, centered.

@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Coin(Drifter):
    """Pickup. Sits still in the world and moves down only with the scroll. Collected on touch:
    it pays its points and leaves a points popup. drifters/04-coin.md."""
    drifter_type: ClassVar[DrifterType] = DrifterType.COIN
    parked: ClassVar[bool] = True
    points: int = 0                   # from the variant
    glint: bool = False               # from the variant
    body_height: int = 0              # from the type, and every value below
    ring_width: int = 0
    ring_height: int = 0
    glint_size: int = 0
    glint_left: int = 0
    glint_top: int = 0
    popup_ticks: int = 1
    popup_rise_per_tick: float = 0.0

    @classmethod
    def born(cls, birth: Birth) -> Self: ...          # ACTIVE from birth: no entry warning
    @classmethod
    def start_position(cls, x: float | None, y: float | None, width: float, height: float,
                       invert: bool) -> tuple[float, float]: ...
        # x is required: None raises ValueError("coin placement needs x"). y None: -height / 2.
    def update(self, ctx: TickContext) -> Self: ...   # y += ctx.scroll_step_px while ACTIVE
    def effect_on_touch(self) -> TouchEffect: ...     # TouchEffect.COLLECT
    def drawn_parts(self) -> tuple[Box, ...]: ...     # the crystal's box, then the ring's box
    def collect_points(self) -> int: ...              # points
    def collect_popup(self) -> PointsPopup: ...       # at (x, y), age 0, popup_ticks, popup_rise_per_tick
```
The fields have defaults so `born_drifter` can build the coin before `born` sets them. Sizes are whole px (the schema asks for even integers), so the view's pixels match the boxes exactly (Rationale). `app.tuning` imports `CoinVariantExtra`, `CoinTypeExtra` and `coin_hitbox` to build the tuning records, so the hitbox is worked out in one place.

## Rules

Coin (`core/drifters/coin.py`, DRA-62). Source: drifters/04-coin.md; scope report DRA-62:
- **Archetype:** Pickup. A parked drifter: it doesn't move on its own, only down with the scroll. Source: archetype, kind (locked); rule 3; 03-world-and-camera.md, rule 9.
- **Variants:** `common`, the default, 50 points, and `rare`, 100 points, with the glint. Same size, same hitbox, same everything else. The tuning file gives each variant's `points` and `glint`; `app.tuning` builds every variant's `width` (12), `height` (20) and hitbox from the type's sizes. Source: variants (common 50 locked, rare 100 guess), default_variant (guess); 06-scoring.md, coin_points; 07-drifters.md, rule 10.
- **Size and hitbox:** the crystal is 12 wide and 20 tall: a 12 × 10 rectangle with a 5 px point above and one below. `width` and `height` are the crystal. The hitbox is one box, the rectangle only: `coin_hitbox(12, 10)`, `Box(0, 0, 12, 10)`. The points, the ring and the glint never count, so the ship must really touch the crystal. Source: crystal_size, hitbox (guess); 07-drifters.md, rule 8.
- **Born:** refuses a specialty (`ValueError("coin has no specialty")`) and an invert (`ValueError("coin has no invert")`), as the base does. Reads `birth.variant_extra`, which must be a `CoinVariantExtra`, else `ValueError("coin variant '<name>' has no points")`, and `birth.type_extra`, which must be a `CoinTypeExtra`, else `ValueError("coin tuning has no type values")`. Then `replace(born_drifter(cls, birth), phase=Phase.ACTIVE, ticks_in_phase=0, ...)` with `points` and `glint` from the variant and every `CoinTypeExtra` value copied onto its field of the same name. Its `speed` is the spawner's 0.0 and its `warning_ticks` the file's 0. Source: entry_warning none (locked); 07-drifters.md, rule 9 and entry_warning_ticks ("Pickups have none"); 91-decision-log.md, row 42; specialty, invert: not in the spec (07-drifters.md, rule 13).
- **No warning of any kind.** It is ACTIVE on the state it is added, so `render_drifter` never draws an entry warning for it, and nothing at all is drawn before the coin itself scrolls in. No telegraph. Source: entry_warning (locked); rules 1 and 2; scope report DRA-62, Limits (Director: "COIN SHOWS NO WARNING").
- **Start:** `start_position`: x is the placement's (required: `ValueError("coin placement needs x")` without it). y is the placement's, or `-height / 2` (−10) when None: the crystal's bottom edge on the top edge, fully off screen. Source: enters_from (locked); rule 1; 07-drifters.md, rules 13 and 14.
- **Update:** in ACTIVE, `y += ctx.scroll_step_px` and `ticks_in_phase + 1`; `x` never changes. In WARNING and GONE, unchanged. The ship in `ctx` is never read. Before the scroll starts it stands still; then it moves 1.1 px a tick at Level 1, exactly as the starfield does. Source: rule 3; kind (locked).
- **Touch:** `effect_on_touch()` is COLLECT. Touching it never hits. No graze zone (base: only HIT has one). Source: rule 4; graze (locked: no); 06-scoring.md, rule 5.
- **Collected** (by the run, `systems/run.md`, step 5a): `collect_points()` is `points`; `collect_popup()` is `PointsPopup(x=x, start_y=y, points=points, lifetime_ticks=popup_ticks, rise_per_tick=popup_rise_per_tick)` at age 0: its center is the coin's center on the tick it is collected. The run then sets it GONE and drops it the same tick: it disappears. An invulnerable ship collects it, and so does a ship that falls below the floor on that tick; a ship standing in the respawn wait doesn't. Those three rules are the run's. Source: rule 4; Edge cases; scope report DRA-62, Limits and Not in GDD (popup start, fall tick).
- **Drawn parts:** `drawn_parts()` is `(Box(x, y, width, height), Box(x, y, ring_width, ring_height))`: the crystal's box, 12 × 20, and the ring's box, 22 × 8, both centered on the coin. The ring is wider than the crystal, so it counts at the sides. The view draws every pixel inside these two boxes moved by the center's rounding (Presentation, Coin), so when both boxes are fully past an edge nothing of the coin is on screen. Source: 07-drifters.md, rule 12 ("every part counts", the ring included: scope report DRA-62, Values needed); 91-decision-log.md, row 64.
- **Leaving:** the base rule on those boxes. It starts fully above the top edge, so it is never removed before it has entered. Once it has, it is removed when its crystal's top edge is at or below the floor (y ≥ 490 at the 20 px height). A coin not collected is lost: nothing pays for it. Source: rule 5; 07-drifters.md, rule 12.
- **Scales:** nothing. Its points, its size, its popup and its movement never change with level; `as_level` is accepted and changes nothing. Source: rule 6.
- **Values** (all guess but `common` 50 and the locked rows): points 50 and 100; crystal 12 × 20, body 10; ring 22 × 8; glint 2 × 2 at (3, 3); `popup_ticks` 60; `popup_rise_per_tick` 0.5. Source: Values table; scope report DRA-62, Not in GDD (rise 0.5 px a tick and the glint, both Director approvals).
- It accepts `x`, `y`, `variant` and `as_level`. `invert`, a specialty and `speed` are refused. Drifters pass over it with no effect, and it never blocks. Source: 07-drifters.md, rules 13 and 15; drifters/04-coin.md, Edge cases.
