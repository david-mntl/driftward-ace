Score: 7.0 | Lowest: 6 | Size: 8

Asset: electric-ball-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/electric-ball-d1-r1.png
Board: staging/assets/sprites/electric-ball-d1-r1-board.png
Measured: 24 × 24 px, 1 frame (still image, no animation frames by design)
GDD: 12-art-and-audio.md, drifters/10-electric-ball.md, 07-drifters.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | The image is 24 × 24 px, which matches `art_canvas` (`guess`). The ball sits centered and the arcs reach toward the edge, as the spec allows. I can't measure the ball's diameter, so I can't confirm the 16 px `ball_size` (`guess`). On the board the body and halo fill most of the canvas, with the arcs close to the edges. The ball has no hitbox in the spec (only the firing circle does), so there is nothing to cover. |
| 2 | World fit | 7 | A bright white-cyan core inside a soft violet halo with thin fuchsia arcs matches `look_reference` ("a pale white-cyan core with thin purple and fuchsia arcs") and the plasma-orb direction. It looks like a charged, glossy orb, which suits "The light" and the mood. The six arcs are short and stubby, so the shape reads as a spiky star more than as crackling lightning. |
| 3 | Colors | 7 | Core is pale white-cyan (electricity) and the arcs are purple at the top and fuchsia at the bottom, as the color language asks. Nothing sits near the ship's cobalt. The halo is a flat lavender, close to the arcs' purple, so the arcs lose contrast against it. The bottom and side arcs are fairly saturated pink: rule 6 lets hazards carry fuchsia only as thin accents, and these are at the edge of "thin". |
| 4 | Light & glow | 7 | The core is hot and white and the halo fades out smoothly, so the ball glows as hazards should (GDD 12 `glow`). The bottom arc is the brightest fuchsia, which fits the bottom-side rim (rule 8). The glow is soft, with no hard white highlight; "The light" calls for hard white highlights, and the core could carry one. The halo is wide enough that it eats into the margin the arcs need. |
| 5 | Readability & finish | 6 | At 1× on the dark navy board (left) it reads as a small, fuzzy lavender dot with a bright center. The arcs are about one pixel wide and short, and several blur into the halo. The edge of the halo looks slightly noisy next to the clean core. Against the purple-tinted backdrop in the third board panel it separates less. Pillar 2 asks for hazards readable at a glance: the white core carries it, the arcs don't. |

## Fix first
- Readability & finish: make the six arcs longer and clearly separated from the halo. Reach toward the canvas edge and keep a gap between them and the halo's edge. Lower the halo's lavender fill, or darken it toward navy, so the arcs stand out.
- Colors and light: keep the fuchsia on the arcs thin, with the bottom arc the strongest. Add one hard white highlight on the core to match "The light".
