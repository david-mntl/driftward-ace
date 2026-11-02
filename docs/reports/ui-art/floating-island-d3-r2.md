Score: 7.6 | Lowest: 7 | Size: 9

Asset: floating-island-d3
Kind: sprite
Round: 2
Image: staging/assets/sprites/floating-island-d3-r2.png
Board: staging/assets/sprites/floating-island-d3-r2-board.png
Measured: 320 × 120 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md
Direction followed: design 3, broken plate (cracked green-tinted stone slabs, dark seams)
Previous report: docs/reports/ui-art/floating-island-d3-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 is exactly the rectangle's `art_canvas` and size (`guess`). On the board the green runs to all four sides of the hitbox outline, with no transparent edge, so the ground fills the box and the ship stops where the ground is drawn (spec rule 10). The 4× master size (1280 × 480) was not given to me, so I did not check it. |
| 2 | World fit | 7 | Pentagon and hexagon slabs with near-black navy seams follow the "broken plate" direction. Cracked ground fits "Planets crack into floating islands" (world brief). The glossy slab shading and hard white seam highlights fit "The light". It still reads as cracked paving more than as a chunk of ground floating in space. The box must stay full, so there is no broken outline, but nothing inside (such as a darker underside or a few chipped slab corners) says "floating". The mood is calm, not horror, which is right. |
| 3 | Colors | 8 | The green is now one family. Slab tones differ only slightly, so the surface reads as one ground, which was the main r1 problem. It matches `look_reference` (green floating ground with a darker edge). The darker green edge shows on the left, right and bottom, and the seam shadows are deep navy. The solid fuchsia band from r1 is gone, so rule 6 (solid bright fuchsia means a coin) is no longer in conflict. The top edge has a pale strip in place of a darker green edge, so the edge is not dark all the way round. |
| 4 | Light & glow | 7 | The bottom fuchsia rim is now a thin line, about 1 px at game size, as rule 8 asks ("thin fuchsia rim on its bottom side"). It is still fully saturated and runs the full 320 px unbroken, so it is the brightest single line on the sprite. A softer, partly faded rim would sit better with the slab shadows. Seam highlights are hard and white and lit from the top-left, which is consistent. A pale strip still runs along the top edge, across the full width, ignoring the slab edges. It reads as a flat bar, not a highlight on a slab. No glow is correct: GDD 12 `glow` covers hazards, warnings and coins only. |
| 5 | Readability & finish | 7 | At 1× on the navy background the island reads clearly as a solid green block with a slab pattern, and the shape is easy to tell from the background. Cracks are down to four, each longer and clearer, and the small white tick glints are gone, so the noise from r1 is much reduced. Weaknesses: the white seam highlights are stair-stepped on their diagonals in the 4× board view (for example the slab edges at upper center and middle right). The seams are heavy and near-black, so the pattern is busy and a bit graphic at 1×. |

## Fix first
- Light & glow: replace the flat pale strip on the top edge with a highlight that follows the top slab edges. Fade the bottom rim in places so it is not one unbroken saturated line.
- World fit and Readability: add a cue that the ground floats, for example a darker bottom tone inside the box, or chipped slab corners that stay inside it. Smooth the stair-stepped white seam highlights on the diagonals.

## Since round 1
- Size: 9 to 9, unchanged. The box is still filled edge to edge.
- World fit: 7 to 7, unchanged. The slab look is the same, and there is still no sign of floating.
- Colors: 7 to 8. The slab tones are narrower and the solid fuchsia band is gone.
- Light & glow: 6 to 7. The rim is thinner and no longer a band. The flat top strip is still there.
- Readability & finish: 7 to 7. The tick glints and extra scribbles are gone, but the diagonal highlights are still stair-stepped and the seams are heavy.
