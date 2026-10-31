Score: 7.8 | Lowest: 7 | Size: 9

Asset: fireball-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/fireball-d2-r1.png
Board: staging/assets/sprites/fireball-d2-r1-board.png
Measured: 64 × 64 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md
Direction judged: design 2, burning rock (dark rock head wrapped in flame, ember sparks in the trail)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` (`guess`). On the board's hitbox overlay the head circle (r16) is filled edge to edge by the rock and its flame ring, so the sprite covers the head hitbox. The tail circle (r8) sits on the flame body behind the head, so it is covered too. The head sits low right and the trail runs up and left inside the canvas, as the spec says. I judged the head position from the overlay, not from measured pixels. The trail tip at the top left is thin and faint, so the tail's far end looks slightly weak. |
| 2 | World fit | 8 | Fits "Stars die and are dragged in, still burning" (world brief, what it does). A dark cracked rock inside a hot flame shell reads as a burning body, and it matches `look_reference` (orange-yellow comet, fading trail). Mood is beautiful and doomed, not horror. The rock reads as a plain grey-brown stone with little "wet, glossy" light, so it feels a bit less like the world's glossy look. |
| 3 | Colors | 8 | Orange to yellow flame matches "heat, danger" in the color language. The fuchsia is only a thin accent on the lower left edge, so it does not claim rule 6. The rock's brown-grey interior is slightly muddy next to the clean flame. The orange cracks in the rock tie it to the flame. A deeper navy-leaning shadow on the rock would match "shadows go deep navy". |
| 4 | Light & glow | 7 | Rim light (rule 8) is present: a thin fuchsia and pink line on the bottom-left edge of the head, the side facing the black hole. It starts a bit past the head and runs on along the flame, so it is slightly heavy at the bottom-left. The flame itself is the glow, bright at the head's edge and fading along the trail, so "hazards glow hot" is met. There is no hard white highlight on the rock, which rule "highlights are hard and white" (world brief, the light) asks for. The glow is only the flame, with no soft halo around the head. |
| 5 | Readability & finish | 7 | At 1× on the dark and on the painting, the bright flame ring clearly separates the head from the background, and the shape reads as a diving comet pointing down-right (Pillar 2). The rock interior is dark and its cracks are small, so it reads as a dark blob at 1×. Ember sparks in the trail are single square pixels that look blocky at 4×, and the trail edge is a little ragged rather than smooth. The small 42 px version stays readable. |

## Fix first
- Light & glow: add a small hard white highlight on the rock's upper-left (side away from the black hole). Keep the fuchsia rim only on the bottom side and thin, and stop it where the head ends.
- Readability & finish: lighten the rock a bit (navy-leaning shadows, a few more visible cracks) so it does not read as a flat dark blob at 1×. Smooth the ember sparks and the trail edge so they are not single hard squares.
