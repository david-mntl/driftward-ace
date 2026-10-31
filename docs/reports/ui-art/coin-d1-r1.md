Score: 7.4 | Lowest: 7 | Size: 8

Asset: coin-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/coin-d1-r1.png
Board: staging/assets/sprites/coin-d1-r1-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md (07-drifters.md not needed: pickup, no entry warning)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, which matches `art_canvas` (`guess`). The faceted crystal sits centered, and the ring spans the middle as the spec asks. On the 4× zoom the crystal body covers the faint 12 × 10 hitbox outline, with the triangle points above and below it. I can't measure the crystal's own 12 × 20 or the ring's 22 × 8 by eye, so I did not score those to the pixel. |
| 2 | World fit | 8 | Follows the direction well: a bipyramid crystal with a spiral galaxy inside and a thin elliptical ring around it. It reads as the "small crystal with a galaxy turning inside" from the world brief, and it is glossy with a hard highlight. The cloud from `look_reference` is hard to see; the galaxy is mostly a spiral with a dark core. |
| 3 | Colors | 7 | Solid bright fuchsia-pink on the facets and the ring owns the coin color (rule 6) and stands out on the navy. The lit crimson side and the dark purple shade side are separate, and the spiral's near-black core is clear. The `look_reference` asks for red, black and purple. The result leans pink, with little red or black showing in the facets at 1×. The palette's black-purple shade side is lighter than its (70, 0, 60) value, so the crystal looks flat pink at game size. |
| 4 | Light & glow | 7 | Coins in play are meant to glow (GDD 12 `glow`). A soft pink halo surrounds both frames, and the ring is the brightest line. The rare frame has a small white glint at the upper left and a stronger halo, as the spec asks ("the rare one shines more"). The rim light (rule 8) is not clearly stronger on the bottom edge: the pink outline runs evenly around the whole crystal, so the side facing the black hole does not stand out. The common and rare frames are close at 1×; the extra shine is easy to miss. |
| 5 | Readability & finish | 7 | At 1× on the board the coin reads as a pink gem with a ring, and nothing else on screen shares that shape. The galaxy inside is too small to read at 1×; it shows as a dark smudge. At the 4× zoom, the glow pixels around the edge are soft and slightly blurry, so the outline loses crispness. The master at 8× is clean. |

## Fix first
- Colors: push the shade side and the spiral core toward the black-purple and near-black palette values so the facets show red, black and purple, not one pink.
- Light & glow: put the brightest rim on the bottom edge (rule 8), and make the rare frame's glint and halo clearly stronger than the common's at 1×.
