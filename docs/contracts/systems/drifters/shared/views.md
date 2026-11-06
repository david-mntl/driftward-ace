# Drifters, views and the entry warning
Part of: drifters
Read when: you change how drifters are drawn: view registry, brightness, entry warning, shapes.

## Diagram

Views:
```mermaid
flowchart LR
  APP["app.frame"] -- "each obj in run.drifters" --> R["ui.drifters.registry.render_drifter"]
  R -- "WARNING" --> W["ui.drifters.entry_warning.draw_entry_warning<br/>(one plain warning sign, the same for every drifter)"]
  R -- "ACTIVE" --> V["registered view at obj.brightness()<br/>render_meteorite, render_satellite,<br/>render_chain_lightning, render_fireball,<br/>render_coin (DRA-62), render_floating_island (DRA-86),<br/>render_planet (DRA-96), render_ufo (DRA-104),<br/>render_electric_ball (DRA-111)"]
  R -- "GONE" --> N["nothing"]
```

## Interface

### game/ui/shapes.py
The line shape from DRA-47, the polygon from DRA-86. Signatures unchanged.
```python
# Imports: pygame, math, core.collision. Never app.
def draw_shape(
    surface: pygame.Surface, color: tuple[int, int, int], shape: Shape, width: int = 0
) -> None:
    ...
    # One placed shape. width 0 fills it; width 1 draws a 1 px outline. Raises
    # TypeError("unknown shape kind '<class name>'") for anything not a Circle, a Box, a Line or a
    # Polygon (DRA-47, Polygon from DRA-86).


def draw_hitbox(
    surface: pygame.Surface, color: tuple[int, int, int], hitbox: Hitbox, width: int = 0
) -> None:
    ...
    # draw_shape for every shape, in order.
```

### game/ui/drifters/
```python
# game/ui/drifters/registry.py. Imports: pygame, math, core.drifters.base, ui.drifters.entry_warning. Never app.
DrifterView = Callable[
    [pygame.Surface, Drifter, tuple[float, float], float, float], None
]
# view(surface, obj, center, scale, brightness): draw obj's look centered at center (screen px),
# scaled by scale (1.0 full size, 0.5 half size), every color multiplied by brightness
# (0..1, 1.0 normal) through dim_color. DRA-39 adds brightness.


def dim_color(color: tuple[int, int, int], brightness: float) -> tuple[int, int, int]:
    ...  # DRA-39
    # Each channel times brightness, rounded half up: math.floor(channel * brightness + 0.5).


def register_view(drifter_type: DrifterType) -> Callable[[DrifterView], DrifterView]:
    ...
    # Decorator. Raises ValueError("view for drifter type 'meteorite' is already registered").


def registered_views() -> frozenset[DrifterType]: ...
def render_drifter(surface: pygame.Surface, obj: Drifter) -> None:
    ...
    # WARNING: draw_entry_warning(surface, obj). ACTIVE:
    # view(surface, obj, (obj.x, obj.y), 1.0, obj.brightness()).
    # GONE: nothing. Raises ValueError("no view registered for drifter type 'x'").

# game/ui/drifters/entry_warning.py. Imports: pygame, math, functools, itertools,
# core.drifters.base. Never app.
ENTRY_WARNING_COLOR: Final[tuple[int, int, int]] = (
    255,
    158,
    94,
)  # #ff9e5e. 07-drifters.md, entry_warning_color (guess)
ENTRY_WARNING_SIZE: Final[int] = 24  # core/drifters/base.py, not ui. 07-drifters.md,
# entry_warning_size: the sign's diameter, the same for every drifter (guess)
FILL_ALPHA: Final[float] = 0.26  # 07-drifters.md, entry_warning_look (guess)
OUTLINE_WIDTH: Final[float] = 1.5  # px. 07-drifters.md, entry_warning_look (guess)
MARK_WIDTH: Final[float] = 1.4  # px, the mark's bar. Placeholder choice, from the WARNING card
MARK_BAR: Final[tuple[float, float]] = (0.32, 0.68)  # shares of the triangle's height
MARK_DOT: Final[tuple[float, float]] = (0.84, 0.056)  # center and radius, same shares


def draw_entry_warning(surface: pygame.Surface, obj: Drifter) -> None:
    ...  # blit the one sign image centered on round(obj.warning_center()).


# game/ui/drifters/__init__.py: imports every view module once (meteorite_view, satellite_view
# from DRA-39, chain_lightning_view from DRA-47, fireball_view from DRA-56, coin_view from DRA-62,
# floating_island_view from DRA-86, planet_view from DRA-96, ufo_view from DRA-104,
# electric_ball_view from DRA-111), so each view
# registers. A package docstring and nothing else. Import lines sit in sorted order
# (ruff's import-sort rule): electric_ball_view goes between coin_view and fireball_view.
```

## Presentation

Every fact a view shows is a core field or a core method. No view works out a rule.

| Core field or method | Shown as |
|---|---|
| `obj.phase` | `render_drifter` picks what to draw: the entry warning in WARNING, the drifter in ACTIVE, nothing in GONE. Source: 07-drifters.md, rule 9 |
| `obj.warning_center()` | the center of the entry warning. Source: 07-drifters.md, rule 9; drifters/01-meteorite.md, rule 1; drifters/02-satellite.md, rule 1; drifters/03-chain-lightning.md, rule 2 (DRA-47) |
| `obj.x`, `obj.y` | the center of the drifter's look while ACTIVE |
| `obj.width`, `obj.height` | the size of the drifter's look. The entry warning does not read it: it has one fixed size |
| `obj.hitbox` | the satellite's look: its two boxes, filled (DRA-39). Source: drifters/02-satellite.md, placeholder_look. The fireball's look: its two circles, filled, head and tail (DRA-56). Source: drifters/06-fireball.md, placeholder_look |
| `obj.nodes`, `obj.node_size` | the chain lightning's nodes: where each sits around `center`, and how big (DRA-47). Source: drifters/03-chain-lightning.md, placeholder_look, node_size |
| `obj.firing_arcs()`, `obj.arcs`, `obj.arc_width` | which arc bands are drawn, between which nodes, how thick (DRA-47). Source: drifters/03-chain-lightning.md, rules 5 and 9, placeholder_look |
| `obj.charge_ray_count()`, `obj.charge_rays`, `obj.ray_length`, `obj.ray_width` | how many rays each node shows now, how they are spread, how long and how thick (DRA-47). Source: drifters/03-chain-lightning.md, telegraph, charge_rays, ray_length, placeholder_look |
| `obj.brightness()` | the share of normal brightness the look is drawn at: `rehit_dim` (0.75) during the re-hit cooldown, 1.0 otherwise. Source: 05-lives-and-damage.md, rule 1.5, rehit_dim (guess) (DRA-39). A coin and a floating island never take part in a hit, so they are always 1.0 |
| `obj.width`, `obj.height`, `obj.body_height` (coin) | the crystal: 12 wide, 20 tall, its middle rectangle 10 tall, so each point 5 tall (DRA-62). Source: drifters/04-coin.md, crystal_size (guess) |
| `obj.ring_width`, `obj.ring_height` (coin) | the ring's 22 × 8 ellipse across the crystal's middle (DRA-62). Source: drifters/04-coin.md, placeholder_look (guess) |
| `obj.glint`, `obj.glint_size`, `obj.glint_left`, `obj.glint_top` (coin) | whether the glint shows (the rare coin), and its 2 × 2 square with its top-left at (3, 3) in the crystal's 12 × 20 box (DRA-62). Source: drifters/04-coin.md, placeholder_look; scope report DRA-62, Not in GDD (rare glint, Director approval) |
| `obj.hitbox`, `obj.width`, `obj.height` (floating island) | the island's look: its shapes filled, their union exactly, with a 2 px darker edge inside it (DRA-86). Its hitbox is the shape drawn, so the ship stops where the ground is drawn. Source: drifters/05-floating-islands.md, hitbox, placeholder_look (guess), rule 10 |
| `obj.width` (planet) | the body: a filled circle `obj.width` across, exactly its hitbox circle (DRA-96). Source: drifters/08-planet.md, size, hitbox, placeholder_look, rule 10 |
| `obj.pull_radius` (planet) | the outer field ring: a 1 px ring at that radius, where the pull starts (DRA-96). Source: drifters/08-planet.md, rule 2, placeholder_look |
| `obj.inner_rings()` (planet) | the inner field rings: for each, a 1 px ring at its `radius`, at its `opacity` (DRA-96). Source: drifters/08-planet.md, field_ring_trip, field_ring_gap, field_ring_fade, rule 10 |
| `obj.hitbox` (UFO) | the UFO's look: the dome circle filled green, then the disc box filled grey over its lower half (DRA-104). `obj.x`, `obj.y` move both, up and down as it weaves; the view never works out the weave. Source: drifters/07-ufo.md, placeholder_look, size, hitbox (guess) |
| `obj.pulse_fires()`, `obj.outline_level()`, `obj.charge_ray_count()` and the size fields (electric ball) | the ball, its charge rays and outline, and its firing circle (DRA-111). The full list is in `electric-ball/view.md`, Presentation. Source: drifters/10-electric-ball.md, telegraph, placeholder_look, rule 9 |
| `obj.drifter_type` | which registered view draws it |
| `obj.variant` | not drawn by these views. The debug label shows it (`docs/contracts/systems/debug-overlay.md`) |

**Brightness** (DRA-39). Every view multiplies each color it draws by its `brightness` argument through `dim_color`: `math.floor(channel × brightness + 0.5)` per channel. `render_drifter` passes `obj.brightness()` in ACTIVE; the entry warning always passes 1.0, because a drifter still warning has never hit. At 0.75 the meteorite's grey (140, 140, 140) becomes (105, 105, 105), the satellite's body (240, 240, 240) becomes (180, 180, 180) and its panel (60, 110, 220) becomes (45, 83, 165). The chain lightning's nodes (0, 220, 255) become (0, 165, 191), its rays (120, 200, 255) become (90, 150, 191) and its arc band (220, 240, 255) becomes (165, 180, 191) (DRA-47). The fireball's head (255, 140, 0) becomes (191, 105, 0) and its tail (200, 160, 0) becomes (150, 120, 0) (DRA-56). The planet's body (140, 70, 200) becomes (105, 53, 150) and its rings (180, 120, 255) become (135, 90, 191), the field dimming with the body (DRA-96). The UFO's disc (170, 170, 185) becomes (128, 128, 139) and its dome (90, 220, 110) becomes (68, 165, 83) (DRA-104). The electric ball's ball, rays, outline, fill and rim dim together, each color through `dim_color` (DRA-111). The drifter returns to its full colors on the first frame drawn from a state whose cooldown has reached 0. A drifter made of parts calls one view, so all its parts dim together. Source: 05-lives-and-damage.md, rule 1.5 and rehit_dim (guess); 91-decision-log.md, row 56.

**Polygon shape** (`ui.shapes.draw_shape`, DRA-86). Every pixel is drawn by the pixel-center rule, so what is drawn matches the shape to within half a pixel and a polygon with whole-px corners never spills past its edges:
- `width` 0 (filled): every pixel whose center lies inside or on the polygon. For each pixel row `r` from `ceil(min_y − 0.5)` to `floor(max_y − 0.5)` (`min_y`, `max_y` the polygon's lowest and highest point y), with `yc = r + 0.5`: `xl` and `xr` are the leftmost and rightmost x where the line `y = yc` meets the polygon (interpolated along each edge that reaches `yc`; a flat edge on `yc` gives both its ends); the row's pixels are the columns `ceil(xl − 0.5)` to `floor(xr − 0.5)`, drawn as one `pygame.draw.rect(surface, color, pygame.Rect(c0, r, c1 − c0 + 1, 1))` when `c1 ≥ c0`. A polygon with whole-px corners and straight up-and-down and across edges fills exactly the pixels a box with the same edges fills.
- `width` 1 (outline): `pygame.draw.polygon(surface, color, [(round(px), round(py)) for each point], 1)`. The debug overlay's polygon outlines come from this, with no change to the overlay.
- Source: 07-drifters.md, rule 8 (a polygon is a filled shape with straight edges); drifters/05-floating-islands.md, rule 10 ("fill the shape exactly").

**Line shape** (`ui.shapes.draw_shape`, DRA-47). With `t = thickness` and `n` the unit normal of AB:
- `width` 0 (filled): the rectangle with corners `A + n t/2`, `B + n t/2`, `B − n t/2`, `A − n t/2`, through `pygame.draw.polygon` (float corners), then a filled circle at A and at B, center `(round(x), round(y))`, radius `round(t / 2)`. With A equal to B, the circle only.
- `width` 1 (outline): the two long sides, `A + n t/2` to `B + n t/2` and `A − n t/2` to `B − n t/2`, as 1 px lines, and the outer half of each end circle (radius `round(t / 2)`) as a 1 px arc. With A equal to B, a 1 px circle outline. The debug overlay's line outlines and graze zones come from this, with no change to the overlay.
- Source: 07-drifters.md, rule 8 (a line with round ends); 91-decision-log.md, rows 47 and 60.

**Entry warning** (`draw_entry_warning`), one plain warning sign, the same image for every drifter, built once and blitted each frame (decision log row 130, 2026-11-02). It shows that a hazard is coming and where, not which one or which way it flies. With `R = ENTRY_WARNING_SIZE / 2 = 12 px`, the warning's outer radius. Source: 07-drifters.md, entry_warning_look, entry_warning_color, entry_warning_size (guess); 91-decision-log.md, row 130:
- **Triangle.** Equilateral, point up, centered on the image's middle pixel (its centroid there), each corner `R − OUTLINE_WIDTH / 2` (11.25 px) from the center, so its round outline never reaches past `R`. Filled in `ENTRY_WARNING_COLOR` at `FILL_ALPHA` (0.26), then outlined in `ENTRY_WARNING_COLOR`, opaque, `OUTLINE_WIDTH` (1.5 px) wide, round at every corner.
- **Mark.** An exclamation mark on the triangle's middle column, opaque `ENTRY_WARNING_COLOR`. With `h` the triangle's height (1.5 × the corner distance) measured down from its apex: a bar from `MARK_BAR[0] × h` to `MARK_BAR[1] × h`, `MARK_WIDTH` (1.4 px) wide with round ends, and a dot centered at `MARK_DOT[0] × h`, radius `MARK_DOT[1] × h` (about 1 px). The proportions copy the WARNING card's sign on the instructions page.
- **Place.** The image's center sits on `round(obj.warning_center())`: for a top entry, at the drifter's x, just inside the top edge; for the satellite, at its y, just inside the wall it enters from (x 12, or 628 with `invert`); for a chain lightning, at the x of the node nearest the ship when it was added, with its center at y 12 (DRA-47); for a fireball, at its head's x against the top edge for a corner or top entry ((12, 12) or (628, 12) for the corners), at its y against the wall for a side entry (DRA-56); for a UFO, at its y against the wall it enters from, (12, y) or (628, y) (DRA-104); for an electric ball, at its x against the top edge, as for the meteorite (DRA-111). Source: 07-drifters.md, rule 9; drifters/02-satellite.md, rule 1; drifters/03-chain-lightning.md, rule 2; drifters/06-fireball.md, rule 1; scope report DRA-29, Decision log (2026-10-15).
- **Pre-rendered.** The image is a `pygame.SRCALPHA` surface, square, side `2 × ceil(R) + 1` (25 px), with the warning's center on its middle pixel, so no pixel of the sign lies more than `R` from the center. It is drawn at 4 times that size and scaled down with `pygame.transform.smoothscale`, so its edges are smooth. Built on the first warning frame of the run and kept for the session (`functools.cache`); it depends on nothing about the drifter, so it is never rebuilt. Source: 12-art-and-audio.md, rule 3 (pre-rendered); 15-tech-constraints.md, rule 5.

Rules for every view:
- Views only draw. They never fill, never flip, never log per frame, never catch an error, never change a drifter, never read the run mode or a key. Source: 10-ui.md, rule 5; game/CONTEXT.md, Run modes.
- A look partly off the surface is clipped by pygame.
- The app calls `render_drifter` for every drifter in `run.drifters`, in order, after the starfield and before the ship (`docs/contracts/systems/app.md`, Draw).
