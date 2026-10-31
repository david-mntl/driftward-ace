Score: 7.4 | Lowest: 6 | Size: 9

Asset: ufo-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/ufo-d2-r1.png
Board: staging/assets/sprites/ufo-d2-r1-board.png
Measured: 40 × 20 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/07-ufo.md, 07-drifters.md
Direction judged: design 2, wrecked (dented hull, cracked green dome, scorch marks, still flying; lights never cobalt)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 40 × 20 matches `art_canvas`. On the board's 4× hitbox overlay, the disc fills the 40 px width and the bottom half of the canvas. The dome circle (radius 9, `guess`) sits over the dome, centered on the disc's top edge. The overlay shows the dome slightly inside the circle at the right edge. I judged the row split only from the board, not from measured numbers. |
| 2 | World fit | 8 | The wrecked direction follows the world brief ("metal ships drift dead, or worse, half alive"). The cracked dome, the dark scorch patches along the hull and the jagged notch in the bottom rim all read as a damaged ship that still flies. The master shows the cracks and dents clearly. At 1× the dents and cracks mostly disappear into the hull texture. The look is "dirty saucer" more than "wrecked saucer". |
| 3 | Colors | 7 | The dome is a clean mid-to-light green, as `look_reference` asks, and it is the brightest, cleanest shape on the sprite. The hull is blue-grey and no light is cobalt. The orange scorch glints and the yellow-orange window lights match "heat, danger" in the color language. The lower hull is dark and slightly muddy: the grey-brown scorch mixes with the navy-grey shading, so the bottom-left of the disc loses definition against the navy. |
| 4 | Light & glow | 6 | The rim is on the bottom side, in fuchsia, as rule 8 asks. It reads as a thin accent at 1×, so rule 6 is respected. The dome has a hard pale highlight at upper left, which fits "The light". There is no soft glow around the sprite. GDD 12 `glow` (a `guess`) says hazards glow, and the board's "1× on a purple glow" strip shows a plain silhouette with no halo. The rim is thick in the master (about 4 px at 8×) and becomes a single broken row of pixels at game size. The notch cuts it in the bottom-right, so the rim has a gap where the damage is. |
| 5 | Readability & finish | 7 | The shape reads at 1× as a saucer with a green dome on the dark background. That is the key read for Pillar 2. The dome is the clear focus. The hull's scorch noise adds speckle across the whole disc, so the silhouette is fine but the interior is busy. The edges at 4× show stepped pixels on the dome and the rim. That is expected from the shrink, but the dome's top edge looks a little blocky. The cracks on the dome are not visible at 1×. |

## Fix first
- Light & glow: add the hazard glow GDD 12 asks for (soft, warm or green, around the sprite), and keep the fuchsia rim continuous and thin along the whole bottom edge, with the notch shown without breaking it.
- Colors / Readability: lift the lower hull's value so it separates from the navy, and cut the scorch speckle to a few clear patches, so the dents and the dome cracks still show at 1×.
