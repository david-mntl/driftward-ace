Score: 7.6 | Lowest: 7 | Size: 8

Asset: coin-d5
Kind: sprite
Round: 1
Image: staging/assets/sprites/coin-d5-r1.png
Board: staging/assets/sprites/coin-d5-r1-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md, 07-drifters.md
Direction: design 5, nebula (a wispy cloud swirling around the crystal, a soft ring)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, which matches `art_canvas`. On the board the crystal is upright and centered, and the 12 × 10 hitbox outline sits on its body. The ring and the cloud stay inside the frame and don't clip at the edges. I can't read exact crystal pixels by eye, so 12 × 20 is judged from the board overlay only. The bottom triangle looks slightly shorter than the top one (`crystal_size`, `guess`). |
| 2 | World fit | 8 | It follows the nebula direction and `look_reference`. There is a faceted crystal with a dark spiral galaxy inside, a pink ring across the middle, and a soft cloud halo. It reads as the "small crystal with a galaxy turning inside" from "The new universe", and it is beautiful and a little unreal. At game size the spiral is a dark smudge, and the cloud is a blocky diamond-shaped haze. It does not read as wisps swirling around the crystal. That only shows in the 8× master. |
| 3 | Colors | 7 | It follows the palette direction: fuchsia and red-pink on the ring and rim, deep purple in the shade, and a near-black galaxy core. It is bright and clean, with no muddy browns. The lit face leans hot magenta-pink rather than the crimson in `palette` (200, 30, 90). The shade side is a soft gradient to plum, not the black-purple (70, 0, 60). The "red, black and purple" fusion in `look_reference` is pushed toward pink and purple, so red is nearly missing. Rule 6 is met: it is clearly the one solid fuchsia shape. |
| 4 | Light & glow | 8 | Coins are allowed to glow (GDD 12 `glow`), and the pink halo does that without hiding the crystal. The brightest pink rim is on the bottom edges of the lower triangle, which follows rule 8. The rare one adds a white sparkle at the upper left of the crystal and a brighter, wider ring, which matches "the rare one shines more". The halo on the rare frame is only a little stronger than on the common one. |
| 5 | Readability & finish | 7 | At 1× the crystal is easy to find on navy, and its shape is clear. Edges on the crystal are clean. The halo edge is stair-stepped at 4× zoom, and the glow fades into the background in blocky steps. The spiral inside is lost, and the ring and cloud blend into one fuzzy diamond. At 1× common and rare differ mainly by the small glint, so they take a second look to tell apart (rule 2: stand out at a glance). |

## Fix first
- Colors: move the lit face toward crimson (200, 30, 90) and the shade toward black-purple (70, 0, 60), so the red, black and purple fusion shows. Keep the ring and rim in bright red-pink.
- Readability & finish: after the shrink, make the cloud a clear thin ring or arc outside the crystal, not a filled diamond haze. Smooth the glow falloff so it doesn't step. Raise the rare frame's glint and ring brightness so common and rare differ at 1×.
