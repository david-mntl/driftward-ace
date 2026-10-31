Score: 7.8 | Lowest: 7 | Size: 8

Asset: floating-island-d2
Kind: sprite
Round: 3
Image: staging/assets/sprites/floating-island-d2-r3.png
Board: staging/assets/sprites/floating-island-d2-r3-board.png
Measured: 320 × 120 px, no frames
GDD: 12-art-and-audio.md, drifters/05-floating-islands.md
Direction: design 2, crystal meadow (green grass ground, a few small dim purple crystals as thin accents).
Previous report: docs/reports/ui-art/floating-island-d2-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 320 × 120 matches the rectangle variant and `art_canvas` (`guess`). On the board the hitbox outline sits on the image edge, with no transparent margin. Not higher because the bottom band (about the lower fifth of the box) is now a dark navy silhouette of hills, with the valleys reaching the bottom row. Next to the navy space background this can read as a hole where the ground is missing. The spec says the ship stops where the ground is drawn (rule 10). The teal outline on the hills and the fuchsia bottom line keep it inside the island, but the ship will stop on that band. |
| 2 | World fit | 8 | The new navy hill silhouette under the strata reads as the dark underside of a broken chunk of planet, so it now says "floating" and "planets crack into floating islands". That was the gap in round 2. The soil falls to deep navy at the bottom ("shadows go deep navy"). The purple crystals tie it to the new-universe look. The grass is still a soft, matte painted texture, not "glossy and wet" (world brief, The light). The soil pebbles are still pale teal blobs and look more like water drops than rock. |
| 3 | Colors | 7 | Green ground with a darker edge follows `look_reference` (`guess`). The grass, the mid-green band, the teal soil and the navy base are clean and well separated. The crystals are now a clearly violet purple, easy to see, and far from coin fuchsia (rule 6). But they are brighter and more saturated than "dim" in the direction, and they are the most vivid thing on the tile. They are the only saturated color other than the grass. A little less saturation in the body would bring them back to dim. The bottom fuchsia line is bright and solid, but only a thin line. |
| 4 | Light & glow | 8 | A thin, hard pale line now follows the grass edge, fixing the soft highlight from round 2. The crystals have small white tips and a lit left face, which matches "highlights are hard and white". A thin fuchsia rim runs along the bottom edge, the side facing the black hole (rule 8). It has no hazard glow, which suits a blocker. Not higher because the left, right and top edges carry no light, and the hill outline is a soft teal, not a hard highlight. |
| 5 | Readability & finish | 8 | At 1× on the board the crystals are now easy to see against the grass, and the six clusters stay a thin accent. The navy hills give a strong dark base and the whole tile separates clearly from the navy background through its green. Edges are smooth, and the grass tufts overlap the crystal bases cleanly. The grass is still a busy streaky texture. The pebbles and the two strata lines are fine detail that turns into noise at 1×. |

## Fix first
- Size: keep the bottom band reading as ground, not a gap. For example, lift the valleys so they don't touch the bottom row, or give the navy base some soil texture or strata. Keep the whole box filled.
- Colors: lower the crystals' saturation a little so they are "dim purple" again. They should be an accent, not the brightest thing on the tile.

## Since round 2
- Size 9 → 8: the dark navy hill band at the bottom can read as empty space inside the hitbox.
- World fit 7 → 8: the hill silhouette under the soil gives the floating-chunk cue that was missing.
- Colors 8 → 7: the crystals are now saturated violet, brighter than "dim".
- Light & glow 7 → 8: the grass-edge highlight is thin and hard, and the crystals have white tips.
- Readability & finish 7 → 8: the crystals read clearly at 1× and the navy base adds contrast. Grass and pebble noise is unchanged.
