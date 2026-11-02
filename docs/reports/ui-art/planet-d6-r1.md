Score: 7.8 | Lowest: 7 | Size: 9

Asset: planet-d6
Kind: sprite
Round: 1
Image: staging/assets/sprites/planet-d6-r1.png
Board: staging/assets/sprites/planet-d6-r1-board.png
Measured: 64 × 64 px, 1 frame (still image, no animation frames, as asked)
GDD: 12-art-and-audio.md, drifters/08-planet.md, 07-drifters.md
Direction for this design: cratered moon in purple-grey. One of several designs, so it is judged against that direction too.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` and `size` (`guess`). On the 4× board the sphere runs edge to edge inside the r32 hitbox circle, with no field rings in the image, as `art_canvas` asks. I can't measure the exact edge pixels, so "exactly" is by eye. The top-left limb looks very slightly soft and dark, so check there that the body touches the circle. |
| 2 | World fit | 8 | A glossy, cratered purple-grey moon fits "The light" (glossy, wet, hard highlights) and the lonely, doomed mood. It follows the direction closely: large craters with dark floors and lit rims. It reads as a planet body, not a rock. Nothing in the image says "anomaly touched" besides the rim, which is enough. |
| 3 | Colors | 7 | Violet and grey-lilac with a navy shadow side matches `look_reference` ("purple sphere") and the fuchsia/purple meaning for the anomaly. The grey in the lit areas is a bit washed. "Colors are more vivid than they should be" asks for more saturation in the mid-tones. The deep navy shadow on the right side is right and not muddy. The fuchsia is only on the rim, so rule 6 holds (solid fuchsia means a coin). |
| 4 | Light & glow | 8 | The rim is fuchsia and runs along the bottom and bottom-right edge, the side facing the black hole (rule 8). It is thin on the lower arc, though it looks a little heavy and bright at the very bottom on the board. The top-left light has hard white highlights on a few crater lips, as the world brief asks. No glow around the body. The GDD gives the planet's glow only to the field rings, which the game draws, so none is needed. |
| 5 | Readability & finish | 7 | At 1× the round silhouette stands out clearly from the navy, and the hitbox is easy to see (Pillar 2). The craters are many and similar in size, so the surface looks a little busy at 1× and the shading steps between them look noisy rather than smooth. The two largest craters read well. The right limb is dark purple-navy and sinks toward the background a little. Edges are clean. |

## Fix first
- Readability & finish: cut the small craters or merge them so 3 or 4 large ones carry the look at 1×. Smooth the shading between craters.
- Colors: raise the saturation of the lit mid-tones toward violet, and lift the right limb a touch so it keeps a readable edge against the navy.

## Notes
- The master PNG (512 × 512) and the `.piskel` file were not given to me and I didn't check them. I judged only the 64 × 64 image and the board.
