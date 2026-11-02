Score: 7.6 | Lowest: 7 | Size: 9

Asset: meteorite-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/meteorite-d4-r1.png
Board: staging/assets/sprites/meteorite-d4-r1-board.png
Measured: 28 × 28 px, 1 frame (still design image)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md
Also looked at: staging/assets/sprites/meteorite-d4-r1-master.png (224 × 224 master, not measured by me; I judged its look only)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 px matches the medium variant (`variants`, `art_canvas`). The round body reaches the edges of the canvas and covers the hitbox circle of radius 14 (`guess`) on the 4× board with the circle ring sitting on the rock's edge. Nothing is cropped. Pumice is round, as the direction asks. |
| 2 | World fit | 7 | A plain rock with no tail and no glow, as `look_reference` asks. The pits are shaded and read as holes. The surface is soft and matte. GDD 12 "The light" asks for glossy, wet, hard white highlights; the top-left highlight is a soft pale wash, not a hard white spot. |
| 3 | Colors | 7 | Warm light grey-tan with dark pits follows the direction and stays clean, not muddy. No orange or yellow, so it does not read as heat (color language). No solid fuchsia (rule 6). The shadow side at bottom right is warm grey-brown, not deep navy as "The light" asks, so the rock looks slightly flat there. |
| 4 | Light & glow | 7 | Thin fuchsia rim on the bottom side, bottom left of the master and visible at 1× as a pink edge under the rock: correct for rule 8, and it is only a thin accent (rule 6). No glow, as `look_reference` says. The rim is a little thin and short at 1× on the painting, and the highlight is soft, not hard white. |
| 5 | Readability & finish | 8 | At 1× on navy and on the painting the pale rock stands out clearly from the background and the round silhouette is easy to read (rule 2). Pits show as dark dots and give a rock texture at 28 px. The edge is smooth in the master. The smallest pits turn to single dark pixels at 28 px and look a little noisy. The 20 px size on the board has the least clean pit pattern. |

## Fix first
- Light & glow / World fit: make the top-left highlight a small hard white spot, so it matches "highlights are hard and white".
- Colors: push the bottom-right shadow toward deep navy instead of warm grey-brown, and let the fuchsia rim run a little longer along the bottom edge so it shows at 1×.
