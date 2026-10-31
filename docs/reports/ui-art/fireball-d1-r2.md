Score: 8.0 | Lowest: 7 | Size: 9

Asset: fireball-d1
Kind: sprite
Round: 2
Image: staging/assets/sprites/fireball-d1-r2.png
Board: staging/assets/sprites/fireball-d1-r2-board.png
Measured: 64 × 64 px, 1 frame (still image, no sheet)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md
Previous report: docs/reports/ui-art/fireball-d1-r1.md

Design direction followed: design 1, classic comet (white-yellow core, orange head, long tapered orange-to-red trail).

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas`. On the board the head fills the head hitbox circle (radius 16, center (44, 44)) edge to edge. The trail now runs bright orange through the whole tail hitbox circle (radius 8, centered near (30, 24), touching the head from behind), so the hit zone is no longer bigger than what the player sees (07-drifters rule 8). That was the r1 gap. The trail points to the top-left and looks close to 35° from straight down (judged by eye, not measured). The tip stays inside the canvas. |
| 2 | World fit | 8 | A burning star dragged in, as the world brief says. Glossy head with a hard white highlight at the upper right and a fuchsia accent at the bottom. It reads as an "Orange-yellow comet with a fading trail" (`look_reference`). Mood is beautiful, not horror. The trail is long and tapered as design 1 asks. |
| 3 | Colors | 8 | Orange and yellow for heat and danger (color language). The core goes white-yellow to orange to deep orange. The trail now stays orange and fades through a warm red instead of the muddy red-brown of r1, and it is clean against the navy. No solid fuchsia shape, so rule 6 holds. The bottom crescent is bright, saturated fuchsia and fairly thick on the 4× board. Keep it a thin accent. |
| 4 | Light & glow | 7 | The hazard glow is added: a soft warm halo follows the trail and wraps the head, pre-rendered (rule 3). The fuchsia rim now sits on the bottom edge of the head, the side facing the black hole (rule 8), and it is continuous, not dotted as in r1. Two small gaps. The halo is thin on the lower right of the head, where the edge still goes from bright orange to navy quickly. The rim crescent is thick at its middle and tapers to nothing at the sides, so it reads more like a magenta shadow than a thin rim. |
| 5 | Readability & finish | 8 | At 1× on the board the head is the brightest thing and the trail shows the direction at once (Pillar 2). The trail holds its brightness further back than in r1, and the tip is still visible. The head edge is smooth on the 4× board, without the r1 stair-stepping. The only soft spot is the trail's far tip: it narrows to a very thin point, and at 1× the last few pixels are faint. |

## Fix first
- Light & glow: thin the fuchsia rim to an even, thin line along the bottom edge. Widen the warm halo on the lower right of the head so the edge does not meet navy so sharply.
- Colors / Readability: keep the trail a little brighter and wider in its last third so the tip stays visible at 1×.

## Since round 1
- Size 8 → 9: the trail now covers the tail hitbox circle, so the tail hit zone matches what is seen.
- World fit 8 → 8: no change.
- Colors 7 → 8: the muddy red-brown back half of the trail is gone; it stays warm orange to red.
- Light & glow 6 → 7: the soft warm halo is added and the bottom rim is continuous. The rim is still heavy in the middle and the halo is thin at the lower right.
- Readability & finish 7 → 8: the trail stays visible further back and the head edge is smooth.
