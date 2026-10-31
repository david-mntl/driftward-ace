Score: 7.6 | Lowest: 7 | Size: 9

Asset: ufo-d3
Kind: sprite
Round: 2
Image: staging/assets/sprites/ufo-d3-r2.png
Board: staging/assets/sprites/ufo-d3-r2-board.png
Measured: 40 × 20 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/07-ufo.md
Direction for this design: half alive, a ribbed organic shell with a green bio dome. No beam. Lights never cobalt.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 40 × 20 matches `art_canvas` (a `guess`). On the board's hitbox overlay, the disc fills the full 40 px width in the bottom half and the dome sits centered on the disc's top edge. The dome circle (radius 9) hugs the green dome well. The disc box (40 × 10) matches the shell. The disc's lower rim sits at the bottom edge of the box. I can't measure the exact bottom row by eye, so check it against the 10 px disc. |
| 2 | World fit | 7 | The glossy green dome with a bright nucleus and the row of glowing orange pores still read as living, and the lights are never cobalt. But the disc is now cleaner and more regular. The master shows evenly spaced plates with straight light and dark bands, which look more like a polished metal saucer than "half alive" (GDD 12: "half alive", "glossy and wet"). The shell has no uneven, organic edge or bulge. Lonely and strange, not horror. |
| 3 | Colors | 7 | Big gain over round 1. The disc is now one lilac-violet family with light ridges and dark navy-violet grooves, and the dithered tan and brown mix is gone. The dome is a vivid, clean green and matches `look_reference`. The orange pores are the only warm accent, close to the heat/danger meaning, but sparse. The lilac-pink of the disc leans toward the anomaly purple. It is not a solid bright fuchsia, so rule 6 holds. A little of the disc's lower half goes pinker. Keep that as a thin accent, not a fill. |
| 4 | Light & glow | 7 | A hard white highlight sits on the upper left of the dome and a pink rim runs along the disc's bottom side, as rule 8 asks. Shadows on the disc are deep navy-violet. The pink rim is about 1 px at game size, near the upper limit of "thin". The hazard glow (GDD 12 `glow`: hazards glow hot) is carried only by the dome and pores. There is no soft halo, so on the purple glow strip the saucer reads less hot than other hazards will. |
| 5 | Readability & finish | 8 | At 1× on the navy the silhouette is clear: green dome on top, flat banded disc, orange pore dots, pink underside. The ribs now read as a few light and dark bands at 4× and still hint at a pattern at 1×. The disc tips are lighter than the navy, so the full 40 px width shows. On the purple glow strip the saucer still separates from the background. The dome pops at a glance (Pillar 2). Edges are smooth and clean. |

## Fix first
- World fit: break up the disc's regular plates. Make the rim edge slightly uneven, and change the band width and spacing so the shell looks grown, not machined. Keep the dome and pores.
- Light & glow: add a small soft hot halo around the dome or pores, so it reads as a hazard (`glow`). Keep the pink rim at 1 px or less on the bottom side only.

## Since round 1
- Colors 6 → 7: the muddy tan, brown and pink dithering is gone and the disc is one lilac-violet family. The pores are still the only warm accent.
- Readability & finish 7 → 8: the ribs now read as clear bands and the disc tips stay lighter than the navy.
- World fit 8 → 7: the cleaner disc lost some of the organic feel from round 1. It reads more like a metal saucer.
- Light & glow 7 → 7: no change. The rim and highlight are still right, and there is still no halo.
- Size 9 → 9: no change.
