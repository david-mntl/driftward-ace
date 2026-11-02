Score: 8.0 | Lowest: 7 | Size: 9

Asset: ufo-d3
Kind: sprite
Round: 3
Image: staging/assets/sprites/ufo-d3-r3.png
Board: staging/assets/sprites/ufo-d3-r3-board.png
Measured: 40 × 20 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/07-ufo.md
Direction for this design: half alive, a ribbed organic shell with a green bio dome. No beam. Lights never cobalt.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 40 × 20 matches `art_canvas` (a `guess`). On the board's hitbox overlay the disc fills the full 40 px width in the bottom half and the dome sits centered on the disc's top edge. The dome circle (radius 9) wraps the green dome closely and the disc box (40 × 10) matches the shell. I can't measure the exact bottom row by eye, so check the disc against its 10 px. |
| 2 | World fit | 7 | Better organic feel than round 2. The ribs are now uneven diagonal bands of different widths, and the dome has fine vein lines around a glowing nucleus, so it reads as a bio dome ("half alive", GDD 12 world brief). The disc outline is still a clean, smooth ellipse with no bulges or uneven edge, so the shell still looks a little machined. The bands read closer to zebra stripes than to ribs. Lights are never cobalt; mood is strange, not horror. |
| 3 | Colors | 8 | The dome is a vivid, clean green and matches `look_reference`. The disc stays in one lilac-violet family with deep violet bands and no muddy mixing. The orange pores are a small warm accent. The only solid bright color is the dome, so rule 6 (solid fuchsia belongs to coins) holds. The peach halo around the outline is a bit milky next to the clean disc colors. |
| 4 | Light & glow | 8 | The round-2 gap is fixed: a soft warm halo now surrounds the saucer in the master, so it reads as a hazard (`glow`: hazards glow hot). The hard white highlight sits on the dome's upper left, and a thin pink rim runs along the bottom side of the disc (rule 8). Deep violet shadows sit on the disc's underside. The halo is faint at 1× on the board and mostly disappears on the navy; the pink bottom rim is carrying most of the warm edge at game size. |
| 5 | Readability & finish | 8 | At 1× on the navy the silhouette is clear: green dome, banded disc, orange pore dots. On the purple glow strip it still separates. The disc bands are readable at 4× and hint at a pattern at 1×. Edges are smooth and clean. The disc's light bands are close in value to the disc tips, so the left and right ends lose a little definition at 1×. |

## Fix first
- World fit: break the disc's outline. Add a slight bulge or notch on the rim and a lumpy lower edge so the silhouette looks grown, not a perfect ellipse. Make the bands follow the shell's curve like ribs.
- Colors / Light & glow (optional polish): keep the halo warmer and tighter so it doesn't wash the disc edge, and make it show at 1×.

## Since round 2
- Light & glow 7 → 8: the soft warm halo now shows in the master, and the white highlight and pink bottom rim stay right.
- Colors 7 → 8: the dome stays vivid and the disc is cleaner, with only a small warm accent.
- World fit 7 → 7: veins on the dome and uneven bands help, but the outline is still a clean ellipse.
- Readability & finish 8 → 8: no change.
- Size 9 → 9: no change.
