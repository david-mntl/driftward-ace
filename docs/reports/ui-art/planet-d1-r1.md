Score: 7.8 | Lowest: 7 | Size: 9

Asset: planet-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/planet-d1-r1.png
Board: staging/assets/sprites/planet-d1-r1-board.png
Measured: 64 × 64 px, 1 frame (still image, no animation frames in this round)
GDD: 12-art-and-audio.md, drifters/08-planet.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` (`guess`). On the board the body touches the r=32 hitbox circle all the way round, as `art_canvas` asks ("filling the hitbox circle exactly"). I can't measure the fill to the pixel from the numbers given, so I did not give 10. No field rings are in the image, as required. |
| 2 | World fit | 8 | A banded gas giant in purples and violets, as the design direction asks. It reads as a planet that the anomaly has touched, and it is glossy as the light rules ask. The pale swirl storm at lower right adds character without turning into a face or a coin. The look_reference "purple sphere" is met. |
| 3 | Colors | 8 | Violet and purple bands with a lighter lavender stripe, clean and well separated, not muddy. It keeps clear of fuchsia, so it does not read as a coin (rule 6). It also keeps clear of the ship's cobalt and the electricity cyan. The darkest bands at lower left are close to the navy background; they are still a purple, not navy, so the body stays closed. |
| 4 | Light & glow | 7 | The hard white highlight at upper left follows "highlights are hard and white". The thin fuchsia rim runs along the bottom edge, on the side facing the black hole (rule 8). Two issues. The highlight is a round white dot, more like a bead than a hard specular on a curved band. The rim is thin and uneven: it is strongest at the lower left and fades toward the lower right. The GDD asks for no glow on this planet, so none was judged. |
| 5 | Readability & finish | 7 | Clear at 1× on the board. The silhouette is a clean circle and the bands survive the shrink. At 4× the outline shows stair-stepped edges on the upper left and right curve, so the shrink left a hard edge instead of smooth antialiasing. The small swirl at lower right turns soft and slightly blurry at 1×. |

## Fix first
- Light & glow: even out the fuchsia rim along the whole bottom arc, and give the highlight a harder, more elongated shape that follows the sphere instead of a round dot.
- Readability & finish: smooth the outline antialiasing on the upper-left and right edges, and keep the swirl crisp at 1×.
