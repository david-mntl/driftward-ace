Score: 7.8 | Lowest: 7 | Size: 9

Asset: coin-d4
Kind: sprite
Round: 3
Image: staging/assets/sprites/coin-d4-r3.png
Board: staging/assets/sprites/coin-d4-r3-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md, previous report docs/reports/ui-art/coin-d4-r2.md
Direction for this design: clean prism with flat facets and a ring of tiny bright specks.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The strip is 48 × 24 with two 24 × 24 frames, which is the `art_canvas` (`guess`). The prism stands upright and centered in each frame, the dark panel sits inside the 12 × 10 hitbox outline on the board, and the ring of specks crosses the crystal's middle (`art_canvas`, `hitbox`, both `guess`). I can't confirm exact crystal and ring pixel sizes by eye; the score rests on the numbers you gave. |
| 2 | World fit | 7 | On the 8× master a clear pink spiral with a near-black core sits in a dark panel, so "a tiny swirling galaxy" (`look_reference`) reads, and the violet haze fits "pure fuchsia and purple, the brightest thing on screen" (GDD 12 world brief). Two gaps from round 2 remain. The crystal body is still opaque, not "transparent". The cloud is only outside the prism, not inside the 24 × 24 square's crystal (`art_canvas`). At the 4× zoom the spiral is a pink swirl in a box, so the galaxy reads, but weakly. |
| 3 | Colors | 8 | Crimson-pink on the lit left facets, black-purple on the right shade side, near-black core and bright red-pink ring follow the coin `palette` (`guess`). It owns solid fuchsia as a coin should (rule 6) and stays clear of hazard orange and electric cyan. The lit facets still lean to light pink-magenta rather than the crimson (200, 30, 90), but the colors are vivid and clean, not muddy. |
| 4 | Light & glow | 8 | GDD 12 `glow` says coins glow. At the 4× zoom the common coin now sits in a visible violet-pink haze, and the 1× row shows a soft pink edge around both coins. On the master a bright lower edge runs along the bottom facets, so the rim leans to the black hole side (rule 8). The rare shines more: a large white-pink star glint at the upper left plus two small sparkles (`palette` rare glint), and a stronger halo, so common and rare differ at 1×. The 1× halo is still subtle on the navy, so it could be a bit wider. |
| 5 | Readability & finish | 7 | At 1× both coins read as small pink gems with dots on each side, and they stand out from the navy (rule 2). The ring specks stay separate dots. At the 4× zoom the shrink is still soft: the facet lines blur into a pink block with stair-stepped edges, and the spiral is a pink swirl without a crisp arm, so the "flat facets" direction is weaker at game size than on the master. |

## Fix first
- Readability & finish: widen the facet separation at 24 × 24 (a darker 1 px line between lit and shade facets) and keep the spiral arm at least 2 px thick so it survives the shrink.
- World fit: show some transparency, for example a lighter, glassier upper facet, and put a hint of cloud inside the square, not only outside it (`look_reference`, `art_canvas`).

## Since round 2
- Light & glow 7 to 8: the common coin's haze now shows at the 4× zoom and the rare's glow is stronger.
- Size 9 to 9, World fit 7 to 7, Colors 8 to 8, Readability & finish 7 to 7: no clear change. The crystal is still opaque, the cloud is still outside, and the facets still go soft at game size.
