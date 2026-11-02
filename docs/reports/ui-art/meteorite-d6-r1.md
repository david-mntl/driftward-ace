Score: 7.8 | Lowest: 7 | Size: 9

Asset: meteorite-d6
Kind: sprite
Round: 1
Image: staging/assets/sprites/meteorite-d6-r1.png
Board: staging/assets/sprites/meteorite-d6-r1-board.png
Measured: 28 × 28 px, 1 frame (still design image, no turn frames yet)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md
Direction followed: chondrite, rounded, sandy brown, speckled with small light grains.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches `art_canvas` and the medium variant (28 px wide). On the board's 4× view the round body reaches the hitbox circle (radius 14, `guess`) on all sides; no gap at the top or left. The bottom rim sits right on the circle edge. Held back from 10 only because the outline is a little ragged where it meets the circle at the right, so the filled area is not a perfect disc. |
| 2 | World fit | 8 | Reads as a plain rock with a hard white highlight at top left and a deep shadow lower right, which fits "The light" (hard white highlights, deep shadows, glossy). No tail and no glow, as `look_reference` asks. The chondrite direction is clear: rounded, sandy, with light grains. The shadow side leans dark mauve-brown rather than the deep navy the world brief names. |
| 3 | Colors | 7 | Sandy tan body with warm shading is clean, well separated from the navy and not muddy. Risk: tan and cream sit close to the yellow/orange "heat, danger" family in the color language, but it is muted enough not to read as lava or fireball. The fuchsia on the bottom is the one saturated color on the rock. On the 4× board it looks like a solid magenta band, not a thin accent. Rule 6 says hazards may carry fuchsia only as thin accents, and a solid bright fuchsia shape means a coin. Keep it a hairline and slightly less saturated. |
| 4 | Light & glow | 7 | The rim is on the bottom side, facing the black hole, as rule 8 asks, and there is no glow, as `look_reference` asks. The highlight at top left is hard and white. Two issues: the rim runs a long way round the lower arc and looks heavy (I can't measure its width by eye, so judged from the 4× board only), and the grains are lit evenly with no sign of the same top-left light, so the lighting does not hold together across the body. |
| 5 | Readability & finish | 8 | At 1× on navy and on the painting the rock is clear at all three scales on the board; the tan body stands out from the dark backgrounds. The speckles read as texture and do not turn to noise. Edges are smooth with no stray pixels. The lower right shadow gets close to the dark painting behind it, so the silhouette softens there; the rim is what keeps the edge visible. |

## Fix first
- Colors: shrink the fuchsia to a thin, less saturated accent so it does not read as a solid fuchsia shape (rule 6). Keep the sandy body as is.
- Light & glow: thin the bottom rim and keep it to the lower side only (rule 8). Make the grains follow the top-left light: brighter on the lit side, dimmer in the shadow.
