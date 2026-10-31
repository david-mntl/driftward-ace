Score: 7.6 | Lowest: 7 | Size: 9

Asset: planet-d2
Kind: sprite
Round: 2
Image: staging/assets/sprites/planet-d2-r2.png
Board: staging/assets/sprites/planet-d2-r2-board.png
Measured: 64 × 64 px, 1 frame (still image)
GDD: 12-art-and-audio.md, drifters/08-planet.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` (`guess`). On the 4x board the body reaches the r=32 hitbox ring on every side, as `art_canvas` asks ("filling the hitbox circle exactly"). The thin teal ring is now hard to see against the body edge, so the fit is better than round 1. I can't measure the fill to the pixel from the numbers given, so I did not give 10. No field rings are in the image, as required. |
| 2 | World fit | 7 | Direction is "cracked rocky planet, as if islands are breaking off" (GDD 12 world brief: "Planets crack into floating islands"). The fissures are now fewer and wider, and a few are thick enough to read as rifts. The body still reads as a cracked ball, close to stained glass. Every plate is flush with its neighbors, and nothing sits raised, tilted or pulled away. The two dark arch shapes in the lower half look like rings or cups, not like a plate breaking off. The mood is calm, not "beautiful and doomed". |
| 3 | Colors | 8 | A clean, vivid purple crust with lighter violet plates at the upper left and deeper violet shadow at the lower right. It is the anomaly color (fuchsia and purple), well separated and not muddy. It keeps clear of the ship's cobalt and the electricity cyan. The fuchsia is held to the rim, so the body does not read as a coin (rule 6). The fissures are deep navy-violet, which fits "shadows go deep navy". The lower right is still darker than the upper left, but it stays purple and does not fall into the navy of space. |
| 4 | Light & glow | 7 | The hard white highlight at the upper left follows "highlights are hard and white". The fuchsia rim now runs thin along the bottom edge, on the side facing the black hole (rule 8), and stays an accent (rule 6). It is clearly better than round 1. Two gaps remain. The highlight is still a blocky white spot, with a stepped edge at 4x, so it looks less glossy than the rim promises. The rim is brighter at the lower right and weak at the lower left. The planet has no glow, which fits: the game draws the field rings. |
| 5 | Readability & finish | 7 | At 1× the disc reads at a glance as a purple planet with large plates, and the shard cluster from round 1 is gone. The lower half is still busier than the top: the two dark arches and the small fissure pieces between them crowd at the bottom. The darkest fissure at the lower left runs close to the outer edge and thins the silhouette there. At 4x the fissure edges and the highlight show stair-steps, so the shrink is not fully smooth. |

## Fix first
- World fit: make the break-up show. Lift or offset one plate, or open one rift wider so it cuts through the outline. Keep the outer circle full so the hitbox still matches. Replace the two arch shapes at the bottom with fissures that read as cracks, not rings.
- Light & glow and finish: smooth the stepped edge of the white highlight and give it a soft falloff. Even out the rim's strength from the lower left to the lower right. Keep the darkest fissure off the outer edge at the lower left.

## Since round 1
- Size 8 → 9: the body now reaches the hitbox circle on every side on the board.
- World fit 6 → 7: the fissures are wider and fewer, so the cracks read more strongly. The plates are still flush, so it is not yet islands breaking off.
- Colors 7 → 8: the rim is now thin, so fuchsia stays an accent. The purple is clean and well separated.
- Light & glow 7 → 7: the rim improved (thin, on the bottom). The highlight is still a stepped blob, and the rim is uneven.
- Readability & finish 6 → 7: the small shard cluster is gone and the big plates read at 1×. The bottom half is still busy, and the edges still show stair-steps at 4x.
