Score: 7.4 | Lowest: 7 | Size: 9

Asset: meteorite-d2
Kind: sprite
Round: 2
Image: staging/assets/sprites/meteorite-d2-r2.png
Board: staging/assets/sprites/meteorite-d2-r2-board.png
Measured: 28 × 28 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md
Direction for this design: iron-nickel, metallic grey-brown, smooth with glossy dents, a sharp white specular spot.
Previous report: docs/reports/ui-art/meteorite-d2-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (one still frame, 28 × 28). On the 4× panel of the board the round body reaches the hitbox circle (radius 14, `guess`) all around, so the rock fills it. The thin rim at the lower edge sits very slightly inside the circle. |
| 2 | World fit | 7 | A plain rock with no tail and no glow, as `look_reference` asks. The hard white spot and the glossy body fit "The light" in the world brief. The big central dent from round 1 is gone, so it no longer reads as a face. The dents now sit mostly on the right and lower right as dark, flat-looking pits. They read as craters more than as smooth glossy dents with their own small highlights, so the iron-nickel direction is only partly met. |
| 3 | Colors | 7 | The body is still a warm tan-grey with a pale mid-tone, but it reads more grey-brown than in round 1. It is still light for iron-nickel; the metal look needs a darker, cooler core. The shadow at the lower right is darker, close to the navy that "The light" asks for. The fuchsia rim is now a thin line along the bottom, so it works as a thin accent and not as a coin-like shape (rule 6). No orange or yellow is used, which is correct (those mean heat). |
| 4 | Light & glow | 7 | The white specular spot sits at the upper middle to upper right of the body and is sharp and hard, as the direction asks. The fuchsia rim is on the bottom side, facing the black hole, as rule 8 asks, and it is thin. No glow, which fits `look_reference`. There is little gradient around the highlight, so the surface reads closer to matte stone than to wet metal. |
| 5 | Readability & finish | 7 | On navy and on the painting in the board, the rock reads as a round pale object at 1×, and it stands out from the dim background (rule 2). The 20, 28 and 40 px versions all stay legible. Edges look smooth. The dark dents on the right are small and lose a little contrast against the navy where they touch the edge. |

## Fix first
- World fit: give each dent a small glossy highlight on its upper edge and a smooth shaded floor, so they read as polished dents and not flat dark pits.
- Colors: darken and cool the body toward grey-brown metal, keeping the tan only as a mid-tone. A darker core will also make the white spot stronger.

## Since round 1
- Colors 6 → 7: the fuchsia rim is now thin (rule 6 satisfied), and the lower-right shadow is darker. The body is still light for iron-nickel.
- World fit 7 → 7: the face-like central dent is gone, but the new dents are flat pits and still miss "glossy dents".
- Light & glow 7 → 7: the rim is now thin, as rule 8 asks. The highlight still has little gradient around it.
- Size 9 → 9, Readability & finish 7 → 7: no change.

Not scored: the 8 turn frames. They come later from the chosen design.
