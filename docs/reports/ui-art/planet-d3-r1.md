Score: 7.2 | Lowest: 6 | Size: 9

Asset: planet-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/planet-d3-r1.png
Board: staging/assets/sprites/planet-d3-r1-board.png
Measured: 64 × 64 px, 1 frame
GDD: 12-art-and-audio.md, drifters/08-planet.md (07-drifters.md not needed: the planet's entry warning is not part of this image)
Direction for this design: lavender ice planet with swirling storms (from the task).

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The measured 64 × 64 matches `art_canvas` and `size`. On the board the disc touches the radius-32 hitbox ring all round and the corners are empty, so it fills the hitbox circle as the spec asks. The field rings are correctly left out. I can't count pixels by eye, so I can't confirm the fill is exact to the pixel. |
| 2 | World fit | 7 | Glossy, wet-looking swirl with a hard white streak fits "The light" in the world brief. It follows the lavender ice storm direction: one big vortex with a smaller storm at the right edge and a long band at the lower right. The disc is almost flat. The swirl runs to the limb with no darkening, so it reads more like a spiral galaxy or a marble than a sphere. Give the edge some roundness. |
| 3 | Colors | 7 | Lavender, violet and white sit inside the purple/magnetism family of the color language, and the planet is clearly not a coin: no solid fuchsia body (rule 6). The upper half is clean and vivid. The lower half and the long band at the lower right turn grey-lilac, which looks muddy against the saturated top. A few teal-green pixels show on the right edge near the middle of the board view. Teal is not a color of this world, so they look like a stray edge pixel. |
| 4 | Light & glow | 6 | The thin fuchsia rim is on the bottom side, mainly the lower left, as rule 8 asks, and it is thin enough not to read as a coin (rule 6). There is a hard white highlight inside the vortex eye. The shadow side (right and bottom) stays mid purple, not the deep navy, almost black, that the world brief asks for, so the light has no clear direction and the rim has nothing to contrast with. The rim also stops short of the right side of the lower edge. No outer glow is drawn, though `glow` includes hazards. This is a judgment call: the spec only asks for a purple sphere, and the pull field is the planet's main mark. |
| 5 | Readability & finish | 7 | At 1× on the board the planet is easy to find on the navy background, and the big swirl gives it a clear shape. The 1× view is busy: many light and dark bands of similar value mean the swirl only partly shows at game size. The edge has a small stair-stepped fringe at the top left and right, and the teal pixels noted above. Nothing blurs or smears. |

## Fix first
- Light & glow: darken the right and bottom shadow side toward deep navy, keep the hard white highlight on the lit side, and run the fuchsia rim along the whole bottom curve.
- Colors / World fit: darken the lower half so it stays purple rather than grey-lilac, shade the limb so the disc reads as a sphere, and remove the teal-green pixels on the right edge.
