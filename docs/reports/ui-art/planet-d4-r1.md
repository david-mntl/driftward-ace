Score: 7.6 | Lowest: 7 | Size: 9

Asset: planet-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/planet-d4-r1.png
Board: staging/assets/sprites/planet-d4-r1-board.png
Measured: 64 × 64 px, 1 frame
GDD: 12-art-and-audio.md, drifters/08-planet.md
Direction for this design: inside out, purple crust with glowing orange fissures from the core.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The measured 64 × 64 px matches `art_canvas`. On the board the sphere touches the r32 hitbox ring all round, so it fills the circle as `size` and `hitbox` ask. No field rings are in the image, as the spec says. I can't check the exact edge pixels by eye. |
| 2 | World fit | 8 | It follows the direction closely and matches the world brief line "It turns a planet inside out": cracked purple crust with hot orange fissures. The surface is glossy and wet, as "The light" asks. It reads as a planet from the anomaly. It could be read as a lava rock, but the purple crust and round shape keep it a planet. |
| 3 | Colors | 7 | Purple crust and orange fissures follow the color language (orange means heat and danger). Both are vivid. In the lower middle of the sphere, the area under the big fissure, the orange bleeds into a brown smear. It looks muddy against the clean purple. The lower-right plates are dark blue-violet and sink toward navy. The fuchsia is only a rim, so rule 6 holds. |
| 4 | Light & glow | 7 | There is a hard white highlight at the top left, as "The light" asks. The fissures glow, which suits a hazard (`glow`: hazards). The fuchsia rim runs along the bottom, the side facing the black hole (rule 8). The rim is bright and about 2 to 3 px thick at the bottom centre, and it is the brightest fuchsia on the sprite. Rule 6 allows only thin accents, so thin it down and let it fade toward the sides. The white highlight is a single blob. A tighter spot with a short streak would read as a hard highlight. |
| 5 | Readability & finish | 7 | The round silhouette is clear at 1× against the navy board. Edges are smooth, with no stray pixels. The fissure network is dense at 1×. Many thin orange lines on the lower half turn into noise, so the planet reads as a busy ball rather than a few bold cracks. The upper-left crust is dark purple and the boundary there is softer than at the bottom. |

## Fix first
- Colors: clear the brown smear under the main fissure in the lower middle. Keep the orange yellow-to-orange and the purple clean. Lift the lower-right plates a little so they do not sink into navy.
- Light & glow / Readability: thin the bottom fuchsia rim and fade it out toward the sides. Cut the number of thin fissures in the lower half to a few bold ones, so the cracks read at 1×. Make the highlight tighter and harder.
