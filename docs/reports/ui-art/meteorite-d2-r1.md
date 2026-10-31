Score: 7.2 | Lowest: 6 | Size: 9

Asset: meteorite-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/meteorite-d2-r1.png
Board: staging/assets/sprites/meteorite-d2-r1-board.png
Measured: 28 × 28 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md
Direction for this design: iron-nickel, metallic grey-brown, smooth with glossy dents, a sharp white specular spot.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (one still frame, 28 × 28). On the 4× panel of the board the round body reaches the hitbox circle (radius 14, `guess`) all around, so the rock fills it as `art_canvas` asks. The outline looks very slightly inside the circle at the lower right, where the rim is thin. |
| 2 | World fit | 7 | A plain rock, no tail, no glow, as `look_reference` asks. A hard white highlight at upper left and a glossy surface fit "The light" in the world brief. The large dark dent in the middle of the body, with two smaller dents below it, reads a bit like a face at 4×. The surface looks more like tan stone than polished iron-nickel, so the direction is only half met. |
| 3 | Colors | 6 | The body is a warm tan and grey-brown, but it is mid-bright and flat. It is not clearly metallic: iron-nickel needs a cooler grey in the mid-tones and a darker core. The lower right shadow looks dark grey-violet, not the deep navy that "The light" asks for. The magenta rim is bright and saturated at the bottom. Rule 6 allows fuchsia only as a thin accent on hazards, and at 1× the crescent is strong enough to risk looking like a coin color. No orange or yellow is used, which is correct (those mean heat). |
| 4 | Light & glow | 7 | The sharp white specular spot at the upper left matches the direction and the "hard, white highlights" line. The fuchsia rim is on the bottom side, facing the black hole, as rule 8 asks. There is no glow, which fits `look_reference` ("no tail and no glow"). The rim reads as a wide crescent along the bottom, not a thin line, and the highlight is a single small spot with little glossy gradient around it. |
| 5 | Readability & finish | 7 | On the navy background and on the painting in the board, the rock reads as a round grey object at 1×, and it separates from the dim background as rule 2 asks. The 28, 20 and 40 px versions all stay legible. Edges look smooth. The dark dents and the dark lower right edge lose some contrast against the navy, so the silhouette softens there. |

## Fix first
- Colors: push the body toward a cooler, darker metallic grey-brown with deep navy shadows at the lower right. Keep the warm tan only as a mid-tone accent, so it reads as iron-nickel and not stone. Make the fuchsia rim thinner so it stays a thin accent (rule 6).
- World fit: make the dents smoother and glossier, with their own small highlights. Break up the big central dent so it does not read as a face.

Not scored: the 8 turn frames. They come later from the chosen design.
