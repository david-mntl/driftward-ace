Score: 8.0 | Lowest: 7 | Size: 9

Asset: demo-ship
Kind: sprite
Round: 2
Image: staging/assets/sprites/demo-ship-r2.png
Board: staging/assets/sprites/demo-ship-r2-board.png
Measured: 32 × 32 px, 1 frame (32 × 32 px)
GDD: 12-art-and-audio.md, 04-ship.md, 07-drifters.md (rule 8)
Previous report: docs/reports/ui-art/demo-ship-r1.md

The ship's `look` is TBD (SH-06). This round is scored against `look_reference` and the color language row for the ship, both `guess`.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 32 × 32 matches `ship_w` × `ship_h` (guess). On the 4× crop, the fuselage now reaches the top edge at full width, so the 12 px bar of the inverted-T `hitbox` (guess) is covered from top to bottom, which fixes the empty bar corners at the nose from round 1. The foot, below the faint green line, is filled by the lower wing plating. Its outer bottom corners are dark charcoal and hard to tell from the black, so the visible edge of the foot is weak there (04-ship.md rule 8, 07-drifters.md rule 8). |
| 2 | World fit | 8 | The wings are now long swept blades with thin tips angled down and out. That matches "long blade-like wings: alien and elegant" in `look_reference`. With no rim and no fuchsia, the ship reads as "untouched" ("You" in the world brief). The shadows on the lower wings and the rear corners are a neutral dark grey, not the "deep navy, almost black" that "The light" asks for. |
| 3 | Colors | 8 | The engine flame at bottom center is blue and there is no fuchsia anywhere, both as the ship's color language row and `look_reference` ask ("a blue flame", "No fuchsia"). The cobalt spine and wing lines sit cleanly against the pale plating in the upper half. The lower half (the rear wing roots and the foot corners) turns to a flat, muddy grey with dim blue lines, so the pale-and-cobalt contrast fades there. |
| 4 | Light & glow | 8 | No fuchsia rim on the bottom edge, so rule 8 is met ("The ship has none: it is untouched"). The flame reads as the ship's own blue, not a hazard's heat glow. The plating has soft gradients and the blade leading edges catch a pale highlight. The hard white highlight that "The light" asks for is faint, mostly a light blue on the spine near the nose. How much the ship itself glows is TBD (SH-06), so that part is not scored. |
| 5 | Readability & finish | 7 | At 1× on the board the ship reads at a glance as a pointed craft with swept wings against the black `placeholder_bg` (guess). Edges are clean and the blade tips stay sharp, with no stray pixels on the 4× crop. The bottom third is dark grey on black, so at 1× the rear of the ship and the foot of the hitbox fade out and the ship looks shorter than it is. That matters most at the bottom of the screen, where falling costs a life (Rule 2, Pillar 2). |

## Fix first
- Readability & finish: lighten the lower wing plating and the foot corners toward the pale plating of the upper hull, so the whole hitbox area reads at 1× on the dark background.
- World fit: push the shadows on the lower wings from neutral grey to deep navy, and add one hard white highlight on the nose or spine ("The light").

## Since round 1
- Size: 8 to 9. The nose now fills the top of the hitbox bar. The faint foot corners keep it from 10.
- World fit: 5 to 8. The fuchsia rim is gone and the delta wings became swept blades. The shadows are still grey, not navy.
- Colors: 3 to 8. The flame is blue instead of orange to yellow, and the solid fuchsia bottom line is gone.
- Light & glow: 3 to 8. No rim, so rule 8 is met. The flame no longer glows in the heat colors.
