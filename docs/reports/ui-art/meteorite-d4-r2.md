Score: 8.0 | Lowest: 7 | Size: 9

Asset: meteorite-d4
Kind: sprite
Round: 2
Image: staging/assets/sprites/meteorite-d4-r2.png
Board: staging/assets/sprites/meteorite-d4-r2-board.png
Measured: 28 × 28 px, 1 frame (still design image)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md
Also looked at: staging/assets/sprites/meteorite-d4-r2-master.png (look only, not measured by me)
Previous report: docs/reports/ui-art/meteorite-d4-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 px matches the medium variant (`variants`, `art_canvas`). The round body reaches the canvas edges and covers the hitbox circle of radius 14 (`guess`); on the 4× board the circle ring sits on the rock's edge and nothing is cropped. The shape is round, as the pumice direction asks. |
| 2 | World fit | 8 | A plain rock, no tail, no glow (`look_reference`). The pits are fewer and larger, and each has a dark inner shade and a lit lip, so they read as holes in a wet-looking surface. The master shows the surface a bit glossier than round 1. The top-left light is still a wide pale wash; GDD 12 "The light" says highlights are hard and white. |
| 3 | Colors | 8 | Warm light grey-tan body with dark pits follows the direction and stays clean, not muddy. The bottom-right shadow now goes cooler and deeper, nearer the deep navy "The light" asks for, so the form turns better than in round 1. No orange or yellow (not heat) and no solid fuchsia (rule 6). The shadow still carries some warm brown at its mid-edge. |
| 4 | Light & glow | 7 | The fuchsia rim now runs longer along the bottom-left edge in the master and shows as a pink edge under the rock at 1× on navy and on the painting. It is a thin accent only (rule 6, rule 8). No glow, as `look_reference` says. The top-left highlight is still a soft wash, not a small hard white spot, and at 4× it reads as a pale patch of pixels, not a highlight. |
| 5 | Readability & finish | 8 | At 1× the pale rock stands out clearly from navy and from the painting, and the silhouette is easy to read (rule 2). The larger pits survive the shrink as clear dark marks and look less noisy than round 1, in all three board sizes (20, 28, 40). The master edge is smooth. A few pits near the rim of the 28 px image fall to one or two dark pixels and the edge there looks slightly lumpy at 4×. |

## Fix first
- Light & glow: replace the soft top-left wash with a small hard white spot (GDD 12 "The light"), sized so it still shows as a bright dot at 28 px.
- World fit / Colors: take the last warm brown out of the bottom-right shadow edge and move it fully to deep navy.

## Since round 1
- World fit 7 → 8: pits are larger and shaded as holes, and the surface reads glossier.
- Colors 7 → 8: bottom-right shadow now cooler and deeper, closer to navy.
- Light & glow 7 → 7: the rim is longer and shows at 1×, but the highlight is still soft, so the score holds.
- Readability & finish 8 → 8: larger pits read better at 28 px, but a few rim pits still shrink to single pixels.
- Size 9 → 9: no change.
