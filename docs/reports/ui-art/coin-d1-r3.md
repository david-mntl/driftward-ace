Score: 8.0 | Lowest: 8 | Size: 8

Asset: coin-d1
Kind: sprite
Round: 3
Image: staging/assets/sprites/coin-d1-r3.png
Board: staging/assets/sprites/coin-d1-r3-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md (07-drifters.md not needed: pickup, no entry warning)
Previous report: docs/reports/ui-art/coin-d1-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, which matches `art_canvas` (`guess`). On the 4× zoom the crystal is centered, the ring spans its middle, and the body covers the faint 12 × 10 hitbox outline with the points above and below. I can't measure the crystal's own 12 × 20 or the ring's 22 × 8 by eye, so those are not scored to the pixel. |
| 2 | World fit | 8 | Follows the "classic" direction and the world brief's "small crystal with a galaxy turning inside": a faceted bipyramid with a split lit/shade face, a spiral galaxy with a dark core, a thin elliptical ring, a hard white glint on the rare one. Beautiful and a bit hopeful, not horror (mood). The cloud from `look_reference` is still hard to tell apart from the spiral. |
| 3 | Colors | 8 | Red, black and purple separate: the upper left is a bright pink-red, the right and lower faces drop to deep purple, and the core is near black (`palette`, `look_reference`). The ring and rim are bright pink-red and own the coin color on navy (rule 6). The lit face still leans pink-magenta more than crimson (200, 30, 90), and the shade face is still lighter than black-purple (70, 0, 60) in the 4× zoom. |
| 4 | Light & glow | 8 | The bottom of the crystal's lower point and the lower arc of the ring are the brightest edges, so the side facing the black hole reads (rule 8). Both coins now show a soft pink halo around the ring in the game-size 4× zoom, so the common coin still glows after the shrink (`glow`, coins). The rare frame has a clear white glint at the upper left and a wider halo, so it shines more, as the spec asks. The top points still carry a light pink outline close in strength to the sides; dim it a little more for a cleaner bottom-only rim. |
| 5 | Readability & finish | 8 | At 1× on the board both coins read as a pink gem with a ring, and no hazard shares that shape (Pillar 2, rule 2). The common and rare differ at a glance by the glint and halo. Edges in the 4× zoom are clean, with no stray pixels. The galaxy inside is still too small to read at 1×; it shows as a dark swirl smudge. The 8× master is clean. |

## Fix first
- Colors: push the lit face nearer crimson (200, 30, 90) and the shade face nearer black-purple (70, 0, 60), so it is less pink.
- Light & glow: dim the rim along the top points so the bottom edge is the only strong rim (rule 8). Make the galaxy arms a little brighter so the spiral shows at 1×.

## Since round 2
- Light & glow 7 → 8: the common coin keeps a visible halo at game size, and the rim favors the bottom edge.
- Size, World fit, Colors, Readability & finish: unchanged at 8.
