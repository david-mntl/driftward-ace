Score: 7.8 | Lowest: 7 | Size: 9

Asset: meteorite-d5
Kind: sprite
Round: 1
Image: staging/assets/sprites/meteorite-d5-r1.png
Board: staging/assets/sprites/meteorite-d5-r1-board.png
Measured: 28 × 28 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md

Direction followed: split rock, two chunks along one crack, a very thin dim purple vein in the crack.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas`. On the 4x board the body reaches the hitbox circle (r14, `guess`) on all sides, so it covers the hitbox and is not bigger than what the player sees (07 rule 8). The bottom-right edge sits slightly inside the cyan circle. |
| 2 | World fit | 8 | A plain glossy rock with no tail and no glow, as `look_reference` asks. The diagonal crack from top right to lower left gives two chunks, as the direction asks. The hard white-lilac highlight at the top left and the deep navy shade on the right fit "The light" (glossy, hard highlights, navy shadows). The body is a fairly smooth lump. A few chipped notches on the outline would make it look more like broken rock. |
| 3 | Colors | 7 | Pale lilac body with blue-navy shade is clean and well defined, and it has no orange or yellow (heat) and no electric cyan. The crack is dark navy with a dim purple vein, which keeps fuchsia as a thin accent (rule 6). The pale body is close to the ship's "pale plating" family. A little more grey-brown or warmer stone in the mid tones would keep it apart from the ship (color language: pale plating means you). |
| 4 | Light & glow | 7 | No glow, correct for this drifter. The fuchsia rim is on the bottom side, facing the black hole (rule 8), and the top-left highlight is hard and white. The rim looks heavy on the 4x view: a solid bright magenta band along the whole lower arc. Rule 6 allows fuchsia on hazards only as a thin accent, and a solid bright shape reads as a coin. Thin it and let it fade out toward the sides. |
| 5 | Readability & finish | 8 | At 1x on navy and on the painting the rock reads at once, with strong light-on-dark contrast. The crack shows as a dark diagonal line, so the split reads even at 28 px. Edges are smooth with no stray pixels. The purple vein inside the crack is nearly invisible at 1x. That is fine for an "accent only", but it means the split depends on the dark line alone. |

## Fix first
- Colors: shift the mid tones of the body slightly toward a warmer or greyer stone so it does not read as the ship's pale plating.
- Light & glow: thin the bottom fuchsia rim and fade its ends. Keep it on the bottom side only.

(The 20 and 40 versions on the board hold up: the crack stays visible at 20.)
