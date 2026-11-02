Score: 8.0 | Lowest: 7 | Size: 9

Asset: floating-island-d3
Kind: sprite
Round: 3
Image: staging/assets/sprites/floating-island-d3-r3.png
Board: staging/assets/sprites/floating-island-d3-r3-board.png
Measured: 320 × 120 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md
Direction followed: design 3, broken plate (cracked green-tinted stone slabs, dark seams)
Previous report: docs/reports/ui-art/floating-island-d3-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 320 × 120 is exactly the rectangle's `art_canvas` and size (`guess`). On the board the green runs to all four sides of the hitbox outline, with a dark green border drawn inside the box and no transparent edge. The ground fills the box, so the ship stops where the ground is drawn (spec rule 10). The 4× master size (1280 × 480) was not given to me, so I did not check it. |
| 2 | World fit | 8 | The lower third now darkens to a deep teal-navy with a scalloped, ragged top edge (board, bottom band). It reads as the shaded underside of a chunk of ground, which fixes the r2 gap "nothing says floating". The slabs with near-black navy seams still follow "broken plate" and "Planets crack into floating islands" (world brief). Glossy slab shading and hard white seam highlights fit "The light". Mood is calm, not horror. The scallop line is soft and blurry, so the underside reads a little like water or fog, not rock. |
| 3 | Colors | 8 | One green family across the surface, as `look_reference` asks (green floating ground with a darker edge). The dark green edge now runs on all four sides, including the top, which was a pale strip in r2. Seam shadows are deep navy, and the underside gradient goes to deep navy-green. No solid fuchsia, so rule 6 is respected. The underside is a flat, slightly grey teal that is a bit muddy next to the vivid upper slabs. The world brief asks for colors "more vivid than they should be". |
| 4 | Light & glow | 8 | The bottom rim is now a thin fuchsia line, about 1 px at game size, and it fades in and out along the bottom edge instead of running as one unbroken line. This fits rule 8 (thin rim on the bottom side) and sits better with the dark underside. White seam highlights follow the slab edges and are lit from the top-left, consistent. The flat pale top strip from r2 is gone, and the top now has a thin dark edge. No glow is correct: GDD 12 `glow` covers hazards, warnings and coins only. At 1× the rim is almost invisible against the dark underside, which is fine for a thin accent. |
| 5 | Readability & finish | 7 | At 1× on the navy background the island is a clear solid green block, and its edge is easy to tell from the background. Four cracks are clean and not noisy. The white seam highlights are still stair-stepped on their diagonals in the 4× view (for example the long slab edges at upper center and middle right). The seams are still heavy and near-black, so the slab pattern is busy at 1×. In the dark lower band the slab edges and cracks lose contrast and the shapes get murky. |

## Fix first
- Readability & finish: smooth the stair-stepped white highlights on the diagonal slab edges, and lift the slab edges in the dark lower band so the pattern still reads there. Thin the heavy seams a little.
- Colors / World fit: give the underside a bit more saturation (a deeper green or blue-green, not grey) and a crisper break line, so it reads as rock and not as fog.

## Since round 2
- Size: 9 to 9, unchanged. The box is still filled edge to edge.
- World fit: 7 to 8. The dark underside with a ragged top edge now says "floating chunk".
- Colors: 8 to 8, unchanged. The top edge is now dark green, but the underside is slightly muddy.
- Light & glow: 7 to 8. The rim is broken up and softer, and the flat pale top strip is gone.
- Readability & finish: 7 to 7, unchanged. The diagonal highlights are still stair-stepped and the seams are heavy. The dark band adds a new low-contrast area.
