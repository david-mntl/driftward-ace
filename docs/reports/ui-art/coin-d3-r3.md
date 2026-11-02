Score: 7.8 | Lowest: 7 | Size: 8

Asset: coin-d3
Kind: sprite
Round: 3
Image: staging/assets/sprites/coin-d3-r3.png
Board: staging/assets/sprites/coin-d3-r3-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md (07-drifters.md not needed: a coin has no entry warning)
Previous report: docs/reports/ui-art/coin-d3-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, exactly the `art_canvas` (`guess`). The crystal is upright and centered, the ring crosses its middle, and the glow stays inside each frame on the 8× master. On the 4× zoom the 12 × 10 hitbox outline sits over the crystal's middle and the body is about as wide as the box. I still can't measure the crystal's 12 × 20 by eye, so I don't score higher. |
| 2 | World fit | 8 | A faceted dark crystal with a galaxy core and a double ring fits "small crystals with a galaxy turning inside" (world brief, The new universe) and the `look_reference`. The red, black and purple fusion holds, and the direction (dark crystal, one core, double ring) is followed. At game size the swirl is still a dot, so "swirling galaxy" shows only in the master. The cloud is hard to see at 1×. |
| 3 | Colors | 8 | Better than round 2. The master body now splits into a lit crimson-pink left side and a darker black-purple right side, as the coin `palette` asks (`guess`). The common core now has a near-black center with a pink ring, which uses the (15, 0, 20) core color. On the 4× zoom the split is visible, but the shade side is still lighter than (70, 0, 60). Rule 6 holds: solid bright fuchsia is on the ring, edges and core. |
| 4 | Light & glow | 8 | Coins glow (glow value). Both have a soft pink halo around the ring and crystal. The lower facets are the brightest pink, so the rim sits on the bottom side facing the black hole (rule 8). The rare coin clearly "shines more": a large white-pink diamond core, a glint at the upper left and a small star at the lower right, as `look_reference` and `variants` ask. The common's highlight is small and quiet. |
| 5 | Readability & finish | 7 | On the 4× zoom the ring now reads as a main band with a thinner second line below it, so the double ring survives the shrink better than in round 2. The common core has a firmer dark center with a bright dot, so it no longer blurs into the body. At the 1× strip both coins read as pink gems on navy and the rare is brighter. What is left: at 1× the two rings are still close and read as one thick band, and the common core is only a small dark dot. The outline is stepped pixels, not clean lines. |

## Fix first
- Readability & finish: open the gap between the two rings a little more, so the double ring shows at 1×. Make the common core's bright dot a bit larger so it reads at game size.
- Colors: darken the shade side of the body toward (70, 0, 60) so the lit/shade split holds at 1×.

## Since round 2
- Colors: 7 to 8. The body split is clearer in the master and at 4×, and the common core now has near-black in its center.
- Readability & finish: 7 to 7. The double ring and the core improved at 4×, but both are still weak at 1×.
- Size, World fit, Light & glow: no change (8, 8, 8).
