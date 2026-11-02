Score: 7.0 | Lowest: 6 | Size: 9

Asset: floating-island-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/floating-island-d4-r1.png
Board: staging/assets/sprites/floating-island-d4-r1-board.png
Measured: 320 × 120 px, no frames
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md

Direction for this design: mutated jungle, dark green roots and vines woven into a dense slab.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 matches `art_canvas` and the rectangle variant exactly (`guess`). On the board the ground reaches all four sides of the hitbox outline, with a darker green rim inside it, so the drawn ground and the hitbox match (rule 10). I can't measure alpha by eye; the corners look filled. |
| 2 | World fit | 7 | Woven vines over a dark rock underside with hanging root tips fit "planets crack into floating islands" and "living things mutate" (world brief), and follow the jungle direction. The base is a flat dark teal slab with faint cracks. It reads as a wall of cables more than a chunk of floating ground, and nothing in it feels torn loose or lit by the anomaly. |
| 3 | Colors | 7 | Greens are vivid and clean, with a darker green edge as `look_reference` asks. Green is outside every color-language meaning, so it can't be mistaken for a hazard or a coin (rule 6). Two weak spots: nearly every vine is the same mid green, so depth between layers is flat. The teal base at the bottom goes muddy and grey-blue. The direction says "dark green", and the top two thirds are bright. |
| 4 | Light & glow | 6 | Hard white highlights run along each vine, which fits "The light" (hard white highlights). The fuchsia rim (rule 8) is there, on the bottom side, but it is a hairline of about 1 px along the bottom edge. It is invisible at 1× on the board, and it is a flat straight line that ignores the root tips and the rock outline. No glow is correct for a blocker (glow rule: hazards and coins only). The rim is the gap. |
| 5 | Readability & finish | 6 | At 1× the slab is clearly a solid green block against the navy, and the dark edge holds the silhouette. Inside, the tangle is busy: many same-width vines, thin bright vine tendrils and leaf tips crossing each other make noise at game size. At 4× the vine outlines are stair-stepped and the shading has visible banding steps, which looks closer to pixel art than the "smooth and glossy" style (`art_style`). The bottom rock layer is dim, and the hanging root tips there are thin and low contrast. |

## Fix first
- Light & glow: draw the fuchsia rim thicker (still thin, not solid) along the bottom side and have it follow the rock outline and root tips, so it shows at 1×.
- Readability & finish: smooth the vine edges and the shading steps (draw the master at 4× with anti-aliased gradients, then shrink). Cut the number of thin tendrils, or vary the vine widths, so the slab reads in one glance at 1×.
