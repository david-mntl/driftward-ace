Score: 7.4 | Lowest: 6 | Size: 9

Asset: ufo-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/ufo-d3-r1.png
Board: staging/assets/sprites/ufo-d3-r1-board.png
Measured: 40 × 20 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/07-ufo.md, 07-drifters.md
Direction for this design: half alive, a ribbed organic shell with a green bio dome. No beam. Lights never cobalt.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 40 × 20 matches `art_canvas` (a `guess`). On the board's hitbox overlay, the disc fills the full 40 px width in the bottom half, and the dome sits centered on the disc's top edge. The dome circle (radius 9) fits the green dome closely. The disc box (40 × 10) matches the shell. The disc's pink underside rim reaches the bottom of the box and looks like it pokes a little past it. I can't measure that by eye, so check the bottom row against the 10 px disc. |
| 2 | World fit | 8 | The brief asks for "half alive". The ribbed shell, the row of glowing orange pores along the disc, and the glossy green dome with a bright nucleus read as a living thing, not a clean ship. This suits "Metal ships and satellites drift dead, or worse, half alive" and "glossy and wet". The lights are orange, never cobalt, so the ship's color stays its own. The saucer silhouette still reads as a UFO. Lonely and strange, not horror. |
| 3 | Colors | 6 | The dome is a vivid, clean green and matches `look_reference`. The disc is muddy. At 1× and 4× the ribs mix tan, grey-brown, dusty pink and purple with dithered noise, and no single hue stands out. The color language wants vivid, clean colors ("Colors are more vivid than they should be"). The orange pores are the only clean accent on the disc. They sit close to the heat/danger meaning (orange = lava, fireball, entry warnings), so use them sparingly. Fuchsia is a thin accent only, so rule 6 holds. |
| 4 | Light & glow | 7 | There is a hard white highlight on the upper left of the dome, and a fuchsia rim runs along the bottom side of the disc, as rule 8 asks. Shadows are dark and purple-navy. Two issues. The rim is bright and about 1 px thick at game size, so it is close to the upper limit of "thin". The hazard glow (GDD 12 `glow`: hazards glow hot) is carried only by the dome and the pores. There is no soft halo, so the saucer reads a little less hot than other hazards will. |
| 5 | Readability & finish | 7 | At 1× on the dark navy the silhouette is clear: green dome on top, flat disc below, pink underside. The dome pops at a glance, which helps Pillar 2. The disc's rib pattern turns into noise at 1× with no clear rib shapes, so the "ribbed shell" is only felt, not seen. On the purple glow strip the dark left and right tips of the disc sink a little. Edges are smooth and the dome outline is clean. |

## Fix first
- Colors: clean up the disc. Pick two or three rib tones from one family (for example a warm grey-violet with a lighter ridge) and drop the dithered tan/pink mix, so the ribs stay distinct at 40 px. Keep the dome green and the orange pores as the only bright accents.
- Readability & finish: make the ribs read at 1× as a few clear light and dark bands across the disc. Keep the disc's outer tips lighter than the navy background so the 40 px width still shows.
