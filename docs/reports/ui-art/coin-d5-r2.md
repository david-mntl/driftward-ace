Score: 7.6 | Lowest: 7 | Size: 8

Asset: coin-d5
Kind: sprite
Round: 2
Image: staging/assets/sprites/coin-d5-r2.png
Board: staging/assets/sprites/coin-d5-r2-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md
Direction: design 5, nebula (a wispy cloud swirling around the crystal, a soft ring)
Previous report: docs/reports/ui-art/coin-d5-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, which matches `art_canvas`. On the board the crystal is upright and centered, and the 12 × 10 hitbox outline sits on the crystal body (`hitbox`, `guess`). The ring and halo stay inside each frame and don't clip. I can't read exact crystal pixels by eye, so the 12 × 20 crystal is judged from the board overlay only. The bottom triangle still looks a little shorter than the top one (`crystal_size`, `guess`). |
| 2 | World fit | 8 | It follows the nebula direction and `look_reference`: a faceted crystal, a dark spiral galaxy inside, a thin pink ring across the middle and a soft haze. It matches "small crystals with a galaxy turning inside" in "The new universe" and the mood (beautiful, a little unreal). In the 8× master the ring is now thinner and the haze lighter, so the crystal is the focus. At game size the spiral is still a dark smudge, and the haze is a soft diamond around the crystal, not wisps swirling around it. The swirling cloud shows only in the master. |
| 3 | Colors | 7 | Bright and clean, with no mud. The ring and rim are bright red-pink as in `palette`. The shade side on the right is now darker and closer to black-purple (70, 0, 60), and the core is near black. The lit left face still reads hot magenta-pink, not the crimson (200, 30, 90) in `palette`. The "red, black and purple" fusion in `look_reference` leans pink and purple, and red is still almost missing. Rule 6 is met: it is clearly the one solid fuchsia shape on the dark ground. |
| 4 | Light & glow | 8 | Coins may glow (GDD 12 `glow`). The pink halo lifts the crystal off the navy without hiding it. The brightest rim is on the bottom edges of the lower triangle, the side facing the black hole (rule 8). The rare frame has a larger white sparkle at the upper left of the crystal, a brighter ring and a stronger halo than the common frame, so "the rare one shines more" is clearer than in round 1. The glint (255, 220, 240) is bright. |
| 5 | Readability & finish | 7 | At 1× both crystals are easy to find on navy and the shape is clear. Crystal edges are clean. In the 4× zoom the ring now shows as pink arcs at the left and right sides of the crystal, which helps. The halo edge still steps in blocks around the diamond. The spiral inside is lost at game size. Common and rare differ by the sparkle and the brighter ring, which is easier to see than in round 1 but still needs a second look at 1× (rule 2: stand out at a glance). |

## Fix first
- Colors: push the lit face from hot magenta to crimson (200, 30, 90) so the red, black and purple fusion shows. Keep the shade near black-purple. Keep the ring and rim bright red-pink.
- Readability & finish: after the shrink, make the haze read as a thin arc or two wisps outside the crystal, not a filled diamond. Smooth the halo falloff so it doesn't step. Make the spiral a lighter or higher-contrast shape at 24 px so it doesn't turn into a smudge.

## Since round 1
- No score moved. The changes I can see are real but small: a thinner ring, a darker shade side, a stronger rare sparkle and halo, and a ring that shows as arcs in the game-size zoom. The weaknesses I named in round 1 (lit face not crimson, haze still a diamond, stepped halo, spiral lost at 24 px) are still there, so Colors stays 7 and Readability & finish stays 7.
