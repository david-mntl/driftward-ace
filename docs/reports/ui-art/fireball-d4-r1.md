Score: 6.8 | Lowest: 6 | Size: 7

Asset: fireball-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/fireball-d4-r1.png
Board: staging/assets/sprites/fireball-d4-r1-board.png
Measured: 64 × 64 px, 1 frame (no sheet)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md

Direction for this design (from the brief): dying star, with a corona around the head and a streaming trail.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 7 | The 64 × 64 canvas matches `art_canvas` (a `guess`). On the board the head sits at about (44, 44) and fills the head circle of radius 16 (`guess`), flying down-right at the 35° angle. The weak part is the tail circle (radius 8, touching the head from behind). On the board it sits over the thin, faint part of the trail, and some of the circle is nearly empty dark. Rule 8 says a hitbox is never bigger than what the player sees. The trail needs more body where the tail circle lies, at about 24 px up-left of the head center. |
| 2 | World fit | 7 | A glossy orange ball with a trail toward the top-left reads as a burning star dragged in ("Stars die and are dragged in, still burning"). The head is clean and round. The "corona" the direction asks for is only a thin beaded cream ring on the head's edge. It does not read as a burning halo, so the dying-star idea is weaker than the brief. The trail is straight and thin, so it feels more like a small comet than a streaming star. |
| 3 | Colors | 8 | Heat colors only: a pale yellow core, orange body and a deep red-orange edge. This follows "Orange and yellow mean heat, danger". They are vivid and clean, not muddy, and the gradient from core to edge is smooth. A thin fuchsia line sits on the head's lower right edge, so rule 6 is kept (fuchsia only as a thin accent). The trail fades from orange to dim yellow, but its far end loses color against the navy. |
| 4 | Light & glow | 6 | The fuchsia rim on the head's lower right, the side toward the black hole, follows rule 8, but it is very thin and almost lost against the cream ring. The highlight at the upper left of the head is a soft yellow-white blob, not the "hard and white" highlight from "The light". Glow applies to hazards (`glow`), but there is no soft outer glow around the head. The corona is a hard-edged ring, not a glow, so the head does not look like it burns into the space around it. |
| 5 | Readability & finish | 6 | The head reads clearly at 1× on both the dark and the painting backgrounds (Pillar 2). Finish is the problem. The trail is a thin streak with scattered square specks that look blocky and pixel-like at 4×. The beaded ring around the head has a jagged, noisy edge. `art_style` asks for smooth gradients and clean edges, not pixel art. The trail tip thins out and nearly vanishes before the top-left corner, so the tail is hard to see at 1×. |

## Fix first
- Light & glow, Readability & finish: replace the beaded cream ring with a smooth corona. Use a soft orange-yellow halo around the head, and add a hard white highlight at the upper left. Redraw the trail as a wider, smooth, gradient-faded stream with soft edges instead of square specks.
- Size: widen and brighten the trail where the tail hitbox lies (about 24 px up-left of the head center), so the radius 8 circle is filled by visible fire.

## Since round 0
Not applicable. This is round 1.
