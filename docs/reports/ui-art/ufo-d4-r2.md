Score: 8.0 | Lowest: 7 | Size: 9

Asset: ufo-d4
Kind: sprite
Round: 2
Image: staging/assets/sprites/ufo-d4-r2.png
Board: staging/assets/sprites/ufo-d4-r2-board.png
Measured: 40 × 20 px, 1 frame (no animation frames asked for)
GDD: 12-art-and-audio.md, drifters/07-ufo.md
Previous report: docs/reports/ui-art/ufo-d4-r1.md

Direction for this design: sleek retro, a thin chrome disc and a large bubble dome, green dome, no beam, no cobalt lights.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The measured 40 × 20 matches `art_canvas` (40 × 20, guess). On the board's hitbox overlay the disc fills the bottom box (40 × 10) and the dome sits on the disc's top edge inside the radius-9 circle. The art covers both hitbox shapes and nothing visibly extends past them (rule 9 of GDD 12, rule 8 of 07-drifters.md). The old orange glow that touched the box edge in round 1 is gone. I can't count pixel rows by eye, so the exact fit at the disc ends is judged from the overlay only. |
| 2 | World fit | 8 | Glossy chrome disc and a bubble dome with a hard white highlight fit "The light" in the world brief (glossy, wet, hard white highlights). It follows `look_reference` (saucer, green dome, no beam) and the sleek retro direction: thin disc, large dome. The disc underside is still a mid grey-violet, not the deep navy the brief asks for, so the lower half looks a bit flat next to the dome. |
| 3 | Colors | 8 | The dome is a vivid, clean green with a clear light-to-dark gradient. The yellow-green halo is gone and the outline is crisp against the navy. The disc is a cleaner pale silver-lavender and the muddy mauve-to-orange join at the ends is gone. The small lights on the disc stay orange and yellow, and nothing is cobalt, so the ship's color stays its own. Green is used by no other hazard. The disc shadow is still not deep navy, which keeps this from a 9. |
| 4 | Light & glow | 7 | The rim is now a pink-fuchsia line along the bottom of the disc, as rule 8 asks, and the orange wrap on the top edge is removed. It is a thin accent, so rule 6 holds (no solid fuchsia shape). The cost is that the hot glow around the hazard is almost gone: the dome and the disc top have no soft glow now, and GDD 12 `glow` gives glow to hazards. At 1× on black and on the purple glow it reads as a lit object only by its rim. The pink line is also fairly thick on the 4× view and runs round both disc ends; keep it to the bottom side. |
| 5 | Readability & finish | 8 | At 1× on the board, on the purple glow and on black, it reads at once as a saucer: green dome on top, light disc below. The dome is the focal point and its edge is cleaner than in round 1. At 4× the dome outline is still slightly stepped. The disc's lowest edge is now defined by the pink rim, so it no longer sinks into the navy. |

## Fix first
- Light & glow: bring back a soft warm hazard glow around the dome and the disc top, kept faint so it does not turn the saucer orange again. Thin the pink rim and keep it on the bottom side only (rules 6 and 8).
- World fit: cool the disc underside to a deeper navy shadow, as the world brief's "shadows go deep navy" asks. That also helps Colors.

## Since round 1
- Colors 7 → 8: the yellow-green halo on the dome and the muddy mauve-orange ends of the disc are gone, and the dome outline is crisp.
- Light & glow 7 → 7: the rim now sits on the bottom side and the orange top edge is gone, but the hot glow that GDD 12 asks of hazards was lost in the same change.
- Readability & finish 8 → 8: the disc's lower edge is better defined by the rim, but the dome outline is still slightly stepped at 4×.
- Size 9 and World fit 8: no change.
