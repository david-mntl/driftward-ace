Score: 7.2 | Lowest: 6 | Size: 9

Asset: floating-island-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/floating-island-d3-r1.png
Board: staging/assets/sprites/floating-island-d3-r1-board.png
Measured: 320 × 120 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md, 07-drifters.md
Direction followed: design 3, broken plate (cracked green-tinted stone slabs, dark seams)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 is exactly the rectangle's `art_canvas` and size. On the board the green runs to all four sides of the hitbox outline, so the ground fills the box and the ship stops where the ground is drawn (spec rule 10). The 4× master size (1280 × 480) was not given to me, so I did not check it. |
| 2 | World fit | 7 | Pentagon and hexagon slabs with near-black navy seams match the "broken plate" direction. Cracked ground fits "Planets crack into floating islands" (world brief, What it does). The glossy, wet slab shading fits "The light". It reads as cracked paving more than as a chunk of ground floating in space: there is no uneven or broken outline, because the box must stay full. The mood is calm and beautiful, not horror, which is right. |
| 3 | Colors | 7 | Green with teal and lime shifts between slabs is vivid and clean, and it matches `look_reference` (green floating ground, darker edge). The darker green edge shows on the left, right and top. Shadows in the seams are deep navy, as the light rules ask. Two problems. The bottom edge is a solid, bright fuchsia band the full 320 px wide, so it competes with rule 6 (solid bright fuchsia means a coin). The slab tones differ a little too much from slab to slab, so the surface looks patchy instead of one ground. |
| 4 | Light & glow | 6 | Hard white highlights on the top and left seam edges, with dark seams on the other side, give a consistent top-left light ("highlights are hard and white"). No glow is correct: GDD 12 `glow` is for hazards, warnings and coins only. The rim is on the bottom side, as rule 8 asks, but it is fully opaque, saturated fuchsia and about 2 px thick across the whole bottom. That is a band, not a "thin fuchsia rim", and it is the brightest thing on the sprite. It should be a thinner, softer accent. The flat pale strip along the top edge, from about x 6 to x 314, reads as a flat bar and not as a highlight on a slab. |
| 5 | Readability & finish | 7 | At 1× on the navy background the island is clearly a solid green block, and the seam pattern shows. Edges are crisp and clean. Weaknesses: the dark crack scribbles, mostly about 1 px, and the small white tick glints on several slabs (for example the slab at upper center and the one at lower left) read as noise or stray specks at game size. Some seam highlights look stair-stepped at 1×. |

## Fix first
- Light & glow: thin the bottom fuchsia rim to a soft 1 px accent. Lower its opacity and fade it into the slab shadows (rules 6 and 8). Replace the flat top strip with a highlight that follows the top slab edges.
- Colors: narrow the green shift between slabs so the surface reads as one ground. Keep the darker green edge on the left, right and top. Remove or shrink the white tick glints, and keep only the cracks that help the "broken plate" read.
