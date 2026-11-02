Score: 7.4 | Lowest: 6 | Size: 8

Asset: coin-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/coin-d3-r1.png
Board: staging/assets/sprites/coin-d3-r1-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md (07-drifters.md not needed: a coin has no entry warning)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, exactly the `art_canvas` (`guess`). The crystal is upright and centered, with a ring across its middle. On the 4× zoom the hitbox outline (12 × 10) sits over the crystal's middle and the body looks about as wide as the box. I can't measure the crystal's 12 × 20 from the image, so I'm not scoring higher. The rare frame's glint rays and halo spread past the ring toward the frame edges. Check they aren't clipped. |
| 2 | World fit | 8 | A dark faceted crystal with a galaxy turning inside, a double ring and a cloud: this is "small crystals with a galaxy turning inside" (world brief, The new universe) and the `look_reference`. In the 8× master the swirl arms in the common coin read clearly. The red, black and purple fusion matches the reference. At game size the swirl shrinks to a plain bright blob, so "swirling galaxy" is only in the master. |
| 3 | Colors | 7 | Crimson to bright red-pink edges, black-purple body and a white-pink rare glint follow the coin `palette` (`guess`). They are clean and vivid. The body is almost uniform dark purple, so the `palette` split (lit side crimson, shade side black-purple) is hard to see. The core is bright pink-white, where the `palette` says near black (15, 0, 20). The direction asked for a bright core, so I take that as intended, but the near-black part of the palette is missing. Rule 6, "coins own solid fuchsia": the solid bright fuchsia is only in the rings, edges and core, and the big body is dark. |
| 4 | Light & glow | 8 | Coins glow (glow value, rule 2). Both coins have a soft pink halo around the ring and crystal. The bottom edges of the crystal are the brightest pink, so the rim sits on the bottom side facing the black hole (rule 8). The rare coin clearly "shines more": a large white-pink diamond core, a cross glint at the upper left and a small star at the lower right, as `look_reference` and `variants` ask. Common and rare are easy to tell apart. |
| 5 | Readability & finish | 6 | On the 1× strip both coins read as pink diamonds with a ring, and the rare one is brighter. The crystal's dark body sinks into the navy, so the shape is carried only by its thin outline and the ring. That is weaker than rule 2 ("coins must stand out at a glance", Pillar 2). In the 4× zoom the shrink is soft: the outline breaks into stepped pixels and the two rings merge into one fuzzy band, so the "double ring" is lost at game size. The common core has no hard edge, so it blurs into the ring. |

## Fix first
- Readability & finish: lift the crystal's body or its outline so the shape holds against navy at 1×. For example, add a brighter lit-side fill on one half of the body, as the `palette` already splits it. Make the double ring survive the shrink: give the two rings a clear gap, or make one ring clearly thinner than the other.
- Size: confirm in the master that the crystal is 12 × 20 of the 24 × 24 frame, and that the rare coin's glint rays stay inside the frame.
