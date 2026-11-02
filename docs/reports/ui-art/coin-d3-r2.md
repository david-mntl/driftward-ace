Score: 7.6 | Lowest: 7 | Size: 8

Asset: coin-d3
Kind: sprite
Round: 2
Image: staging/assets/sprites/coin-d3-r2.png
Board: staging/assets/sprites/coin-d3-r2-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md (07-drifters.md not needed: a coin has no entry warning)
Previous report: docs/reports/ui-art/coin-d3-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, exactly the `art_canvas` (`guess`). The crystal is upright and centered with the ring across its middle. On the 4× zoom the 12 × 10 hitbox outline sits over the crystal's middle and the body is about as wide as the box. I still can't measure the crystal's 12 × 20 from the image, so I don't score higher. The rare glint rays (upper left, lower right) and the halo look inside the frame on the 8× master, but I can't confirm that at the pixel edge. |
| 2 | World fit | 8 | Faceted dark crystal, a swirl inside, a cloud and a double ring: this is "small crystals with a galaxy turning inside" (world brief, The new universe) and the `look_reference`. The red, black and purple fusion holds. In the 8× master the common swirl arms read. At game size the swirl is a bright dot in the middle of the crystal, so "swirling galaxy" shows only in the master. |
| 3 | Colors | 7 | Crimson to red-pink edges, a visible lit side on the crystal body and a white-pink rare glint follow the coin `palette` (`guess`). The body is now a brighter magenta-purple than in round 1 and the lit and shade sides can be told apart in the master. This is better. Two things remain. The core is bright pink-white where the `palette` says near black (15, 0, 20). I take that as the direction's "bright galaxy core", but no near-black is left in the core. On the 4× zoom the lit/shade split is still faint: the body reads as one mid pink-purple. Rule 6 holds: solid bright fuchsia is on the rings, edges and core. |
| 4 | Light & glow | 8 | Coins glow (glow value, rule 2). Both have a soft pink halo around the ring and crystal. The lower facets are the brightest pink, so the rim sits on the bottom side facing the black hole (rule 8). The rare coin clearly "shines more": a large white-pink diamond core, a cross glint at the upper left and a small star at the lower right, as `look_reference` and `variants` ask. The common's glint is small and quiet, so the two are easy to tell apart. |
| 5 | Readability & finish | 7 | Better than round 1. The brighter body fills the crystal, so on the 1× strip both coins read as pink gems with a ring and the shape no longer sinks into the navy. The rare is clearly brighter. The weak spot is the shrink. On the 4× zoom the double ring still merges into one stepped band of two pink rows, so "double ring" is lost at game size. The common core is still a soft blob with no hard edge. The outline is stepped pixels, not clean lines. |

## Fix first
- Readability & finish: keep the two rings apart through the shrink. Give them a clear gap of at least one full game pixel, or make one ring much thinner than the other. Give the common core a firmer edge so it doesn't blur into the body.
- Colors: split the body more clearly at game size. A stronger lit side (200, 30, 90) against the shade side (70, 0, 60), and a darker area around the core to use the near-black in the `palette`.

## Since round 1
- Size: 8 to 8. The canvas still fits; the crystal's 12 × 20 is still not measurable by eye.
- World fit: 8 to 8. No change.
- Colors: 7 to 7. The body is lighter and shows a lit side, but the split is faint at 4× and the core still has no near-black.
- Light & glow: 8 to 8. No change.
- Readability & finish: 6 to 7. The body fill makes the shape hold against navy at 1×. The double ring still merges at game size.
