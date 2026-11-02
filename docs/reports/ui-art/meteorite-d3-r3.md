Score: 8.0 | Lowest: 7 | Size: 9

Asset: meteorite-d3
Kind: sprite
Round: 3
Image: staging/assets/sprites/meteorite-d3-r3.png
Board: staging/assets/sprites/meteorite-d3-r3-board.png
Measured: 28 × 28 px, 1 frame (still image, no sheet)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md (shared hazard rules only)
Previous report: docs/reports/ui-art/meteorite-d3-r2.md

Direction for this design: frost-crusted (dark rock, pale white-grey frost on the top half, no cyan, no blue).

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (`guess`). In the board's 4× view the round body touches the r14 hitbox ring on the top, left, right and bottom, as the spec asks ("the rock filling the hitbox circle"). One still frame, as the brief says. Not 10 because I judge the fit only from the 4× view, and the upper-left edge looks a hair inside the ring. |
| 2 | World fit | 7 | A plain rock with no tail and no glow, as `look_reference` asks. The frost is now broken into ragged patches that run across the top and down the right side, with grey crater patches on the lower half, so it reads more as frost on stone than in round 2. It still looks a bit like a cratered moon: the frost blobs are rounded and the outline is a clean circle with no chips or cracks. A broken, anomaly-touched rock (GDD 12, "What it does") would have a less perfect silhouette. Mood (beautiful and doomed) is mild. |
| 3 | Colors | 8 | The body is now a neutral mid grey, no longer cobalt-leaning, so it keeps clear of the ship's blue (color language). Frost is white-grey with no cyan, as the direction says. No orange or yellow, so nothing reads as heat. No solid fuchsia fill, so rule 6 holds. Small gap: the transition from frost to rock is a few flat grey steps, so the lower half looks a touch dull next to the "more vivid than they should be" light in the world brief. |
| 4 | Light & glow | 8 | No glow, as `look_reference` demands. A thin fuchsia rim runs along the bottom edge, the side facing the black hole (rule 8), and stays a thin accent at 1× on navy and on the painting. The hard white frost highlight sits at the top right, opposite the rim, so the light reads as one direction. Small gap: the rim thins out toward the lower left and lower right sides. |
| 5 | Readability & finish | 8 | At 1× on navy and on the painting the full circle reads, and the white frost pops at once (Pillar 2). The grey lower half separates from the navy at 20, 28 and 40 px. Edges are smooth at 1×. In the 4× view the frost edge is still a little blocky in places, and the crater patches on the lower half are low contrast, so the body looks flat. |

## Fix first
- World fit: break the silhouette a little. Add a chip or a flat facet on the edge, and make the frost edge more jagged, so it reads as a broken rock and not a round moon. Keep the body inside the hitbox circle.
- Colors / Readability: lift the contrast of the crater patches and the frost-to-rock steps on the lower half, so the body is less flat. Keep the grey neutral.

## Since round 2
- Size 9 to 9: unchanged.
- World fit 7 to 7: the frost edge is more ragged, but the silhouette is still a perfect circle and the moon look remains.
- Colors 7 to 8: the body is now neutral grey and no longer leans cobalt.
- Light & glow 8 to 8: unchanged. The rim is still continuous at the bottom and still thins at the sides.
- Readability & finish 8 to 8: unchanged. The right-side notch is smoother, but the lower half is still flat.
