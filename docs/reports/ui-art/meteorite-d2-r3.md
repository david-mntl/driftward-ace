Score: 8.0 | Lowest: 7 | Size: 9

Asset: meteorite-d2
Kind: sprite
Round: 3
Image: staging/assets/sprites/meteorite-d2-r3.png
Board: staging/assets/sprites/meteorite-d2-r3-board.png
Measured: 28 × 28 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md
Direction for this design: iron-nickel, metallic grey-brown, smooth with glossy dents, a sharp white specular spot.
Previous report: docs/reports/ui-art/meteorite-d2-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (one still frame, 28 × 28). On the 4× panel of the board the round body touches the hitbox circle (radius 14, `guess`) around most of its edge, so the rock fills it. The thin rim at the lower left sits a hair inside the circle. |
| 2 | World fit | 8 | A plain rock with no tail and no glow, as `look_reference` asks. The hard white spot, the wet-looking body and the fuchsia edge fit "The light" in the world brief. The dents on the right and lower half now have a lighter lip on their upper edge and a shaded floor, so they read as polished dents and not flat pits. That meets the "glossy dents" part of the direction. The dents are a bit many and similar in size, so the rock looks slightly like a cratered moon more than a smooth iron lump. |
| 3 | Colors | 7 | The body is now much darker and cooler, with a deep navy-purple shadow at the lower right, as "The light" asks. But it has gone grey-blue. The direction says grey-brown, and the warm brown tone from round 1 and 2 is nearly gone. A little warm brown in the mid-tone would bring it back without using orange or yellow (heat, color language). The fuchsia is a thin line, so it stays an accent and does not read as a coin (rule 6). |
| 4 | Light & glow | 8 | The white specular spot sits at the upper middle of the body and is sharp and hard, with a visible gradient falling off around it, so the surface now reads as wet metal. The fuchsia rim runs along the bottom-left, the side facing the black hole, and is thin (rule 8). No glow, which fits `look_reference`. The rim looks a little thicker at the lower left than at the bottom, so it is slightly uneven. |
| 5 | Readability & finish | 8 | At 1× on navy and on the painting in the board, the rock reads as a pale round object that stands out from the dim background (rule 2). The 20, 28 and 40 px versions all stay legible. Edges are smooth. The darkest dents on the right lose a little contrast against the navy where they touch the edge, but the outline holds. |

## Fix first
- Colors: add a warm brown to the body's mid-tone so it reads grey-brown, not grey-blue. Keep the dark cool shadow at the lower right.
- World fit: use fewer dents, or vary their size, so the rock reads as smooth iron with a few dents and not a cratered moon.

## Since round 2
- World fit 7 → 8: dents now have a lighter upper lip and a shaded floor, so they read as glossy.
- Colors 7 → 7: the core is darker and cooler as asked, but it overshot into grey-blue and lost the brown.
- Light & glow 7 → 8: a clear gradient around the highlight gives a wet-metal surface. The rim is still thin and on the bottom side.
- Readability & finish 7 → 8: the darker body gives the white spot and the dent lips more contrast, and the rock stands out more on both backgrounds.
- Size 9 → 9: no change.

Not scored: the 8 turn frames. They come later from the chosen design.
