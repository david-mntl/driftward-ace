Score: 7.4 | Lowest: 6 | Size: 9

Asset: electric-ball-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/electric-ball-d3-r1.png
Board: staging/assets/sprites/electric-ball-d3-r1-board.png
Measured: 24 × 24 px, 1 frame (still image)
GDD: 12-art-and-audio.md, drifters/10-electric-ball.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 24 × 24 matches `art_canvas` (`guess`). The glassy ring sits centered and reads as the 16 px ball. The lightning bolts reach the canvas edge at upper right and lower left, as the spec allows. The ball has no hitbox, so nothing needs covering. Small deduction: the upper-right bolt looks close to clipping at the edge on the 8× zoom. |
| 2 | World fit | 7 | The direction (a caged glassy sphere with a knot of lightning) is followed: a pale rim ring, a dark violet interior and a bright white knot. It is glossy, which fits "The light". The `look_reference` asks for a spiky orb, and here the ring is smooth and only 3 or 4 thin bolts break out. At 1× it reads more as a bubble than a spiky electric orb. |
| 3 | Colors | 7 | It follows the electricity row: the core and ring are pale white-cyan, the arcs are purple and fuchsia, and nothing is cobalt, so it stays away from the ship. The fuchsia is a thin bottom arc and thin bolts (rule 6 respected). The mid-ring cyan has a slight blue tint. Inside, the mottled mid-purple and lilac blotches look muddy at 1×. |
| 4 | Light & glow | 8 | Hazards glow, and the soft violet halo around the ring is on the right side of the glow rule. The fuchsia rim runs along the bottom side, the side facing the black hole (rule 8). The white knot at the center reads as a hard highlight. The halo is fairly wide at the zoomed sizes, but it is still inside the canvas. |
| 5 | Readability & finish | 6 | On the dim purple haze at 1×, the ball reads as a purple and white disc with a pale outline, but the lightning knot turns to mush. The bolts inside become blotchy lilac cells, as in the 8× zoom (visible pixel noise). Against the haze the dark violet interior sinks, so the shape loses its center. The edge halo steps look rough in the lower left. |

## Fix first
- Readability & finish: simplify the interior at 24 px. Use fewer, bolder white bolts on a darker, flatter violet fill, so the knot reads at 1×. Drop the lilac blotches.
- World fit: make the bolts at the rim sharper and a little more numerous so the orb reads as spiky, as `look_reference` asks. Keep the glassy ring.
