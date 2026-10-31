Score: 7.8 | Lowest: 7 | Size: 8

Asset: coin-d1
Kind: sprite
Round: 2
Image: staging/assets/sprites/coin-d1-r2.png
Board: staging/assets/sprites/coin-d1-r2-board.png
Measured: 48 × 24 px, 2 frames of 24 × 24 (common, rare)
GDD: 12-art-and-audio.md, drifters/04-coin.md (07-drifters.md not needed: pickup, no entry warning)
Previous report: docs/reports/ui-art/coin-d1-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The strip is 48 × 24 with two 24 × 24 frames, which matches `art_canvas` (`guess`). The crystal is centered, the ring spans its middle, and on the 4× zoom the body covers the faint 12 × 10 hitbox outline with the points above and below. I can't measure the crystal's own 12 × 20 or the ring's 22 × 8 by eye, so those are not scored to the pixel. |
| 2 | World fit | 8 | Still follows the "classic" direction and the world brief's "small crystal with a galaxy turning inside": a faceted bipyramid, a spiral galaxy with a dark core, a thin elliptical ring, a hard white glint on the rare one. The cloud from `look_reference` is still hard to see; it merges into the spiral. |
| 3 | Colors | 8 | The shade side and the lower half of the crystal are now clearly darker, so red, black and purple show against the lit pink-red upper left (`palette`, `look_reference`). The ring and rim stay bright pink-red and own the coin color (rule 6) on the navy. The lit side still leans pink more than crimson (200, 30, 90) at 1×, and the shade side is still lighter than black-purple (70, 0, 60) in the 4× zoom. |
| 4 | Light & glow | 7 | Rim light (rule 8) is better: the lower edge and the lower half of the ring are now brighter than the top, so the side facing the black hole reads. The rare frame has a clear white glint at the upper left and a wide halo, so it shines more than the common one at 1×, as the spec asks. The common frame has almost no glow left in the game-size pixels; GDD 12 `glow` says coins glow, and at 1× the common coin now reads less glowing than its master. The upper edge still carries a pink outline as strong as the sides. |
| 5 | Readability & finish | 8 | At 1× on the board both coins read as a pink gem with a ring, and nothing else shares that shape (Pillar 2, rule 2). Edges in the 4× zoom are cleaner than round 1, with less blur around the outline. The galaxy inside is still too small to read at 1×; it shows as a dark swirl-like smudge. The master at 8× is clean. |

## Fix first
- Light & glow: give the common coin a soft glow that survives the shrink, so it still reads as glowing at 1× (GDD 12 `glow`). Keep the rare halo clearly wider than the common's.
- Light & glow and Colors: dim the rim on the top edge so the bottom edge is clearly the brightest (rule 8), and push the shade side nearer (70, 0, 60) and the lit side nearer (200, 30, 90).

## Since round 1
- Colors 7 → 8: the shade side and lower half are darker, so red, black and purple now separate.
- Readability & finish 7 → 8: outline is crisper at 4× zoom, less blur.
- Light & glow 7 → 7: the rim now favors the bottom and the rare shines clearly more, but the common coin lost most of its glow at game size.
- Size 8 and World fit 8: unchanged.
