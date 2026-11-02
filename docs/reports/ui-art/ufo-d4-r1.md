Score: 7.8 | Lowest: 7 | Size: 9

Asset: ufo-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/ufo-d4-r1.png
Board: staging/assets/sprites/ufo-d4-r1-board.png
Measured: 40 × 20 px, 1 frame (no animation frames asked for)
GDD: 12-art-and-audio.md, drifters/07-ufo.md, 07-drifters.md

Direction for this design: sleek retro, a thin chrome disc and a large bubble dome, green dome, no beam, no cobalt lights.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The measured 40 × 20 matches `art_canvas` (40 × 20, guess). On the board's hitbox overlay, the disc sits in the bottom half and fills the disc box (40 × 10). The dome sits on the disc's top edge and fills the radius-9 circle, so the art covers both hitbox shapes and nothing extends past them (rule 8 of 07-drifters.md). I can't count pixel rows by eye. The rim glow on the disc ends looks like it touches the box edge, so check that it doesn't spill past it. |
| 2 | World fit | 8 | A glossy chrome disc with a hard white highlight on the dome fits "The light" in the world brief (glossy, wet, hard white highlights). The saucer reads as a dead-or-half-alive metal ship. It follows `look_reference` (saucer, green dome, no beam) and the sleek retro direction: the disc is thin and the dome is large. The underside of the disc is mid grey-violet, not the deep navy shadow the brief asks for, so it looks a little flat. |
| 3 | Colors | 7 | The green dome is vivid and clean, with a light-to-dark gradient and a white highlight. Green is not used by any other hazard, so it stands out. The disc lights are orange, yellow and pink, with no cobalt blue, so the ship's color stays its own. The disc body is a pale mauve-grey that gets slightly muddy where it meets the orange rim at the left and right ends. The dome also has a yellow-green halo that softens its edge. |
| 4 | Light & glow | 7 | Hazards glow hot (glow in GDD 12), and this one does: a warm orange-pink edge around the disc and a soft glow around the dome. Rule 8 asks for a thin fuchsia rim on the bottom side only. Here the warm edge wraps the whole disc, top included, and it reads orange more than fuchsia. In the 1× on-black view the underside rim is pink, which is right. Keep that one and move the orange off the top edge. Rule 6 is respected: no solid fuchsia shape. |
| 5 | Readability & finish | 8 | At 1× on the board, on the purple glow and on black, the shape reads at once as a saucer: green dome on top, light disc below. The dome is the clear focal point. The edges are smooth in the master and clean at 1×. At 4× the dome outline looks slightly stepped, and the thin disc's dark lower edge sinks a little into the navy. |

## Fix first
- Colors: clean up the disc ends where the mauve-grey meets the orange rim, and cool the disc underside to a deeper navy shadow. Remove the yellow-green halo from the dome edge so its outline stays crisp.
- Light & glow: keep the pink rim on the bottom side only (rule 8). Take the orange glow off the top edge of the disc and keep the orange to the small lights on the rim.
