Score: 7.2 | Lowest: 6 | Size: 8

Asset: fireball-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/fireball-d1-r1.png
Board: staging/assets/sprites/fireball-d1-r1-board.png
Measured: 64 × 64 px, 1 frame (still image, no sheet)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md

Design direction followed: design 1, classic comet (white-yellow core, orange head, long tapered orange-to-red trail).

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 64 × 64 matches `art_canvas`. On the board the head fills the head hitbox circle (radius 16, center (44, 44)) edge to edge, and the head sits inside the canvas. The trail runs from the head toward the top-left corner, and its direction looks close to the 35° from straight down the spec asks for (judged by eye on the board, not measured). The trail is thinner than the tail hitbox circle (radius 8, touching the head from behind). The circle's outer upper-left edge sits over a very faint part of the trail, so the tail hit zone is bigger than what the player sees (07-drifters rule 8, "never bigger than what the player sees"). Widen the trail near the head, or keep it brighter out to the circle's far edge. |
| 2 | World fit | 8 | A burning star dragged in, as the world brief says. The head is glossy, with a hard white highlight at the upper right of the head and a thin fuchsia accent at the bottom. It reads as a comet with a fading trail, which matches `look_reference` ("Orange-yellow comet with a fading trail"). The mood is beautiful, not horror. |
| 3 | Colors | 7 | Orange and yellow for heat and danger, as the color language says. The core goes white-yellow to orange to deep orange at the rim, and it is vivid and clean. The weak spot is the back half of the trail: it goes to a dark red-brown that looks muddy against the navy. Orange to red is kept, but the red-brown mid-to-end section reads as dirty rather than hot. No solid fuchsia anywhere, so rule 6 holds. |
| 4 | Light & glow | 6 | Rule 8: there is a thin fuchsia rim on the bottom edge of the head, on the side facing the black hole. That is correct. It is only a few pixels wide and looks dotted and uneven along the bottom curve. The `glow` rule says hazards glow hot, and the head has no soft outer glow. The edge goes straight from bright orange to navy, so the head looks flat-edged rather than emitting light. The trail has no glow either. Add a soft warm halo around the head and trail, pre-rendered (rule 3), and keep the bottom rim fuchsia. |
| 5 | Readability & finish | 7 | At 1× on the dark board the head is the brightest thing and stands out at once (Pillar 2). The first third of the trail also reads well and shows the direction. The last third of the trail fades to near-background, so the tip is hard to see at game size. The head edge shows stair-stepping on the right and upper right on the 4× board, and the pink rim pixels at the bottom look noisy. Smooth the edge and the rim. |

## Fix first
- Light & glow: add a soft warm outer glow around the head and along the trail. Make the fuchsia rim on the bottom edge a continuous thin line, not dotted.
- Readability & finish (and Colors): keep the trail orange-red and bright further back instead of fading to dark brown. Widen it near the head so it covers the tail hitbox circle. Smooth the head edge.
