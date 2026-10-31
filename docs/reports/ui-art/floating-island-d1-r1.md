Score: 7.2 | Lowest: 6 | Size: 9

Asset: floating-island-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/floating-island-d1-r1.png
Board: staging/assets/sprites/floating-island-d1-r1-board.png
Measured: 320 × 120 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md, 07-drifters.md (not needed beyond the hitbox rule 8, via the island spec)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches the rectangle variant and `art_canvas`. The ground fills the whole box, and the board's hitbox outline sits on the image edge with no transparent margin, so the hitbox ("the shape itself, exactly as drawn") is covered. A dark green-brown frame about 4 px thick runs around the border, so the edge pixels are darker than the moss. This is fine for "no transparent edge". |
| 2 | World fit | 7 | Follows the direction closely: moss on top, layered strata in the body, darker edge. The glossy, wet moss with hard white specks suits "The light" in the world brief. It reads as a ground cross-section more than a chunk that was cracked off a planet. The slime-like green drips into the rock look more like goo than moss, and nothing in the body hints at the anomaly's mark beyond the bottom line. |
| 3 | Colors | 6 | The moss is vivid, clean green and matches `look_reference` (green ground). The strata are a dull olive-grey and mud brown with soft blurred bands. The world brief says colors are "more vivid than they should be", and these browns read muddy. The grey-green bands (middle band, left side) sit close to the moss's dark shadow and lose definition. The tan pebbles are the only warm accent. Nothing here is orange or yellow, so nothing is mistaken for heat. No fuchsia is used as a solid shape (rule 6). |
| 4 | Light & glow | 7 | Rule 8 is met. A thin bright fuchsia rim runs along the whole bottom edge, the side facing the black hole. It is thin, so rule 6 holds. Hard white highlights are there: the pale streaks near the top of the moss and the white specks across the grass. The island needs no glow (it is not a hazard, warning or coin). Shadows between the moss drips and under the strata are warm brown-black, not deep navy as "The light" says. The bottom rim is the only fuchsia, so the moss gets none of the anomaly's shimmer. |
| 5 | Readability & finish | 7 | At 1× the top surface is clear: a bright green flat edge against the dark background, so the player can see where to stand. The drips under the moss give the top a good silhouette inside the image. The body is busy: dozens of pebbles, thin cracks and white specks across the strata. They add noise and the specks look like background stars. Edges inside the art are soft and blurry, and a faint halftone texture shows in the moss at 1×, so it is not as clean as "smooth and glossy". |

## Fix first
- Colors: lift the strata out of mud. Raise saturation and separate the bands by clear lightness steps, so the grey-green band no longer sits close to the moss shadow.
- Light & glow, Readability: move the shadows toward deep navy instead of brown-black, and cut the pebble and white speck count in the lower body so the top surface stays the clearest thing.
