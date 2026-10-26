# Drifters, the fireball, core
Part of: drifters
Read when: you change how the fireball behaves (`fireball.py`).

## Diagram

Fireball (DRA-56). One drifter: the head is its size and its center, the tail a smaller circle touching it from behind, along its path. Small, Level 1, no `invert`:
```
            tail r 5.25, center at (x - 9.03, y - 12.90)
              o
               \   path: 35° from straight down, 3.0926 px/tick along it
                O  head r 10.5, center (x, y); width = height = 21
                 \
                  v  velocity_x +1.7738, velocity_y +2.5333 per tick
```
Start and warning by entry. `R` = head width ÷ 2. Without `invert` / with it:
```
entry            placement     start (x, y)               warning center           flies
corner           no x, no y    (0, -R) / (640, -R)        (12, 12) / (628, 12)     down right / down left
along the top    x             (x, -R)                    (x clamped to 12..628, 12)
side             y             (-R, y) / (640 + R, y)     (12, y) / (628, y)
```

Fireball timeline, small, Level 1, placed with no x, no y and no `invert` (the top-left corner), added at the end of tick T. `n` counts ACTIVE ticks. Drawn parts: the head's box 24 × 24, the tail's 13.5 × 13.5 (each circle's radius + `DRAW_MARGIN` 1.5, on each side):
```
state after tick   T        T+1..T+59   T+60       T+61      T+60+n               T+258     T+261     T+262
phase              WARNING  WARNING     ACTIVE     ACTIVE    ACTIVE               ACTIVE    ACTIVE    dropped
x                  0.00     0.00        0.00       1.77      n × 1.7738           351.22    356.54    358.32
y                  -10.50   -10.50      -10.50     -7.97     -10.5 + n × 2.5333   491.10    498.70    501.23
hitbox             none     none        2 circles  2 circles
has_entered        no       no          yes        yes
warning shows at   (12, 12), copy turned 35° counterclockwise: head below and right of the tail
```
At T+60 the head's drawn box reaches 1.5 px into the screen, so it has entered. On T+258 (n 198) the head's own circle is fully below the floor, but the tail's drawn box top is at 471.44, on screen: it stays. On T+261 the tail's box top is at 479.04, still on screen. On T+262 it is at 481.58 and the head's at 489.23: every part is off, so the run drops it. At Level 8: speed 3.0926 × 1.42 ≈ 4.3915, velocities ≈ (2.5189, 3.5973); the angle never changes.

Big, `invert`, the top-right corner: starts at (640, −16), tail at (+13.77, −19.66) from the head, r 8; drawn boxes 35 × 35 and 19 × 19. Dropped on n = 208 (x ≈ 271.04, y ≈ 510.93). Small from the left wall at y 120: starts at (−10.5, 120), warning at (12, 120), dropped on n = 150 (x ≈ 255.58, y ≈ 500.00).

## Interface

### game/core/drifters/fireball.py (DRA-56)
```python
# Imports: stdlib (math), core.collision, core.world, core.drifters.base, core.drifters.registry.
DRAW_MARGIN: Final[float] = 1.5   # px added to each circle's radius in drawn_parts(). Not a game value:
                                  # the view draws a circle at a whole-pixel center with a whole-pixel
                                  # radius, each rounded to the nearest, so no drawn pixel lies farther
                                  # than radius + 1.5 from the true center (Rationale)

@dataclass(frozen=True, slots=True, kw_only=True)
class FireballTypeExtra(DrifterTypeExtra):
    """The fireball's values that hold for every variant. Final numbers."""
    angle_degrees: float      # path angle from straight down, degrees, 0 <= angle < 90. Never scaled
    tail_ratio: float         # tail radius as a share of the head's radius, > 0

def fireball_hitbox(head_width: float, tail_ratio: float, angle_degrees: float,
                    invert: bool) -> Hitbox: ...
    # Offsets from the head's center, head first, tail second:
    # (Circle(0.0, 0.0, R), Circle(tail_x, tail_y, tail_ratio × R)), with R = head_width / 2,
    # d = (1 + tail_ratio) × R (the tail touches the head), θ = radians(angle_degrees):
    # tail_x = −d × sin θ, or +d × sin θ with invert; tail_y = −d × cos θ.

@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Fireball(Drifter):
    """Fast linear hazard. Dives in a straight line at a fixed angle from straight down, through
    walls and drifters, never turning. drifters/06-fireball.md."""
    drifter_type: ClassVar[DrifterType] = DrifterType.FIREBALL
    invert: bool = False          # True: flies down and to the left; enters at the right
    angle_degrees: float = 0.0    # path angle from straight down, degrees, from the type
    tail_ratio: float = 0.0       # tail radius ÷ head radius, from the type
    velocity_x: float = 0.0       # px/tick, + is right. Final, set at birth
    velocity_y: float = 0.0       # px/tick, + is down. Final, set at birth

    @classmethod
    def born(cls, birth: Birth) -> Self: ...
    @classmethod
    def start_position(cls, x: float | None, y: float | None, width: float, height: float,
                       invert: bool) -> tuple[float, float]: ...
        # Never raises: no x and no y is the corner start.
    def update(self, ctx: TickContext) -> Self: ...
    def effect_on_touch(self) -> TouchEffect: ...     # TouchEffect.HIT
    def drawn_parts(self) -> tuple[Box, ...]: ...     # one box per hitbox circle, its radius + DRAW_MARGIN
    def warning_tilt_degrees(self) -> float: ...      # +angle_degrees, or -angle_degrees with invert
    def warning_copy(self) -> Self: ...               # itself laid straight down, sized head plus tail
```
The fields have defaults so `born_drifter` can build the fireball before `born` sets them. `app.tuning` imports `FireballTypeExtra` and `fireball_hitbox` to build the tuning records, so the hitbox is worked out in one place.

## Rules

Fireball (`core/drifters/fireball.py`, DRA-56). Source: drifters/06-fireball.md; scope report DRA-56:
- **Archetype:** Fast linear hazard. A moving drifter: its speed is its on-screen speed along its path, and the scroll doesn't add to it. Source: archetype, kind (locked); rule 3; 03-world-and-camera.md, rule 9.
- **One drifter, two circles.** Its size is its head: `width` and `height` are the head width (21 small, 32 big). `x`, `y` is the head's center. The tail is part of it, never a drifter of its own. Source: size; 91-decision-log.md, rows 61 and 64.
- **Variants:** `small`, the default, 21 px head, and `big`, 32 px head. Both fly at the same speed. The tuning file gives each variant's `head_width`; `app.tuning` builds `width` = `height` = `head_width` and the un-inverted hitbox with `fireball_hitbox`. Source: variants, default_variant (guess); 07-drifters.md, rule 10.
- **Hitbox:** two circles, head first. The head: radius `R` = head width ÷ 2 (10.5, 16), on the center. The tail: radius `tail_ratio × R` (5.25, 8), touching the head from behind along its path, its center `(1 + tail_ratio) × R` from the head's (15.75, 24), at `angle_degrees` from straight up behind it: up and to the left without `invert`, up and to the right with it. `fireball_hitbox` is the one place that rule lives. Source: hitbox (guess); 07-drifters.md, rule 8.
- **Born:** refuses a specialty (`ValueError("fireball has no specialty")`). Reads `birth.type_extra`, which must be a `FireballTypeExtra`, else `ValueError("fireball tuning has no type values")`. Then `replace(born_drifter(cls, birth), ...)` with: `invert = birth.invert`; `angle_degrees` and `tail_ratio` from the type; `hitbox = fireball_hitbox(birth.width, tail_ratio, angle_degrees, birth.invert)`; `velocity_x = speed × sin θ`, negated with `invert`; `velocity_y = speed × cos θ`, θ in radians from `angle_degrees`. Final numbers, set once, at birth. The speed already holds the level's hazard speed ×; the angle never scales. Source: rules 3 and 6; specialty (locked).
- **Start:** `start_position(x, y, width, height, invert)`, with `R = width / 2`. A coordinate the placement set is kept. No x and no y: the corner, `(0, −R)`, or `(SCREEN_W, −R)` with `invert`: the head's center on the wall, its bottom edge on the top edge. An x and no y: along the top, `(x, −R)`. A y and no x: a side, `(−R, y)`, or `(SCREEN_W + R, y)` with `invert`: the head's edge on the wall, fully outside it. Both: `(x, y)`. It never raises. Source: start, enters_from (guess, locked); rule 3; 07-drifters.md, rule 14.
- **Update:** in WARNING, `tick_warning(self)`. In ACTIVE, `x += velocity_x`, `y += velocity_y` and `ticks_in_phase + 1`. In GONE, unchanged. No targeting, no turning; the ship in `ctx` is never read. Source: rule 3.
- **Touch:** `effect_on_touch()` is HIT: touching the head or the tail is a hit. Graze zone (base): both circles grown by the drifter's `graze_margin`; the run's graze step pays for it (`systems/run.md`, step 5b). Source: rule 4; graze (locked); 06-scoring.md, rules 3 and 4.
- **Hitting again:** the shared re-hit cooldown. One hazard with one counter: head and tail dim together and keep flying. A touch while the ship is invulnerable is no hit. Source: Edge cases; 05-lives-and-damage.md, rule 1.5.
- **Drawn parts:** `drawn_parts()` is one box per circle of `current position + hitbox`, in hitbox order: `Box(x + c.cx, y + c.cy, 2 × (c.r + DRAW_MARGIN), 2 × (c.r + DRAW_MARGIN))`. Small: 24 × 24 and 13.5 × 13.5. Big: 35 × 35 and 19 × 19. Source: rule 5; 07-drifters.md, rule 12; 91-decision-log.md, row 64.
- **Leaving:** the base rule on those boxes: once it has entered, it is removed only when the head's box and the tail's box are both fully past a side wall or the floor, so nothing of it is still visible when it goes. It flies through the walls and through other drifters. Source: rule 5; 07-drifters.md, rules 12 and 15.
- **Warning place:** the base `warning_center()`. Corner: (12, 12), or (628, 12) with `invert`. Along the top: at its x, against the top edge. Side: at its y, against the wall it enters from. Source: rule 1; 07-drifters.md, rule 9.
- **Warning tilt:** `warning_tilt_degrees()` is `+angle_degrees` without `invert` and `−angle_degrees` with it. The copy lies straight down, head at the bottom; turning it 35° counterclockwise points the head down and to the right, the way it flies; clockwise with `invert`, down and to the left. Source: rule 1 ("tilted along its path, with the tail pointing back").
- **Warning copy:** `warning_copy()` is `replace(self, width=2 × R, height=2 × (1 + tail_ratio) × R, hitbox=(Circle(0.0, tail_ratio × R, R), Circle(0.0, −R, tail_ratio × R)))`, with `R = width / 2`: the comet laid straight down, the tail above the head, touching it, centered on the copy's center. Its longest side is head plus tail (31.5 small, 48 big), so the whole comet fits the 14 px copy. In WARNING like its owner. Source: rule 1; 07-drifters.md, entry_warning_size.
- **No telegraph, no specialty.** The entry warning is its only warning. It accepts `invert`, `variant`, `x`, `y`, `speed` (the debug list) and `as_level`. Source: telegraph, specialty (locked); rule 2; 07-drifters.md, rule 13.
- **Speed at Level 1:** `0.47 × TOP_SIDE_SPEED` = 0.47 × 6.58 ≈ 3.0926 px/tick along its path: ≈ 1.7738 across and ≈ 2.5333 down per tick. Source: speed_ratio, speed (guess, derived); 06-fireball.md, Values note (about 2.5 down and 1.8 sideways).
- A side entry placed so low that it never shows (below the floor) is never removed, as for every drifter (Rationale, DRA-39).
