# Drifters, the chain lightning, view
Part of: drifters
Read when: you change how the chain lightning looks.

## Interface

### game/ui/drifters/
```python
# game/ui/drifters/chain_lightning_view.py (DRA-47). Imports: pygame, math, core.collision,
# core.drifters.base, core.drifters.chain_lightning, ui.shapes, ui.drifters.registry. Never app.
CHAIN_NODE_COLOR: Final[tuple[int, int, int]] = (0, 220, 255)    # drifters/03-chain-lightning.md, placeholder_look (guess)
CHAIN_RAY_COLOR: Final[tuple[int, int, int]] = (120, 200, 255)   # same
CHAIN_ARC_COLOR: Final[tuple[int, int, int]] = (220, 240, 255)   # same
FIRST_RAY_DEGREES: Final[float] = 45.0     # drifters/03-chain-lightning.md, ray_length: the first ray on the
                                           # 45° diagonal (guess). Counterclockwise on screen from pointing right

@register_view(DrifterType.CHAIN_LIGHTNING)
def render_chain_lightning(surface: pygame.Surface, obj: Drifter, center: tuple[float, float],
                           scale: float, brightness: float) -> None: ...
    # Raises TypeError("render_chain_lightning draws a ChainLightning") for any other drifter.
```

## Presentation

**Chain lightning** (`render_chain_lightning`, DRA-47). Any drifter that is not a `ChainLightning` raises `TypeError`. Each node sits at `(center[0] + offset_x × scale, center[1] + offset_y × scale)` for its offset in `obj.nodes`. Drawn in this order, so the nodes sit on the ends of the bands and the rays on top:
1. **Arc bands.** For each index in `obj.firing_arcs()`, the arc's two placed nodes joined by `ui.shapes.draw_shape(surface, dim_color(CHAIN_ARC_COLOR, brightness), Line(ax, ay, bx, by, obj.arc_width × scale))`, filled: a band (220, 240, 255) 6 px thick at full size, exactly the arc's hitbox. Nothing while charging or in the warning. Source: placeholder_look; rule 9 (the hitbox is never bigger than what the player sees); 91-decision-log.md, row 60.
2. **Nodes.** Every node, a filled circle in `dim_color(CHAIN_NODE_COLOR, brightness)`, (0, 220, 255) at full brightness: center `(round(node_x), round(node_y))`, radius `round(obj.node_size × scale / 2)`: 6 at full size, 1 in the entry warning. Drawn always, firing or not. Source: placeholder_look, node_size.
3. **Rays.** Around every node, `obj.charge_ray_count()` rays (0 unless charging). Ray `k` (from 0) points at `FIRST_RAY_DEGREES + k × 360 / obj.charge_rays` degrees, counterclockwise on screen from pointing right: direction `(cos θ, −sin θ)`. It runs from `node + direction × obj.node_size / 2 × scale` (the node's edge) to `node + direction × (obj.node_size / 2 + obj.ray_length) × scale`, drawn with `pygame.draw.line(surface, dim_color(CHAIN_RAY_COLOR, brightness), start, end, max(1, round(obj.ray_width × scale)))`. With 4 rays the order is 45° (up right), 135° (up left), 225° (down left), 315° (down right): one ray up right for the first quarter of the charge, all four for the last. Source: telegraph, charge_rays, ray_length, placeholder_look (guess); 91-decision-log.md, row 62.
- Full size, firing `pair_flat` at (320, 300): a band from (256, 300) to (384, 300), 6 px thick, with a 12 px cyan disc on each end. The warning copy (WARNING: no band, no ray), at the warning's scale of 0.1: three cyan discs of radius 1 in a point-up triangle with 12.8 px sides. Source: placeholder_look; entry_warning_icon (locked).
- No art, no jagged arc, no glow, no flicker, no sound (scope report DRA-47, Out). The charge's "faster" in the GDD's telegraph is left to the real look; the placeholder shows only the growing count.
