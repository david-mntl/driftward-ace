Score: 8.0 | Lowest: 7 | Size: 9

Asset: fireball-d5
Kind: sprite
Round: 1
Image: staging/assets/sprites/fireball-d5-r1.png
Board: staging/assets/sprites/fireball-d5-r1-board.png
Measured: 64 × 64 px, 1 frame (still image)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md
Direction for this design: braided, a trail of two twisting flame ribbons.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | The image is 64 × 64, as `art_canvas` asks (`guess`). On the board's 4× view the head fills its r16 hitbox circle, centered near (44, 44). The braid runs through the r8 tail circle, which sits 24 px back along the 35° path. The trail starts near the top-left, inside the canvas, and is not cut. The trail looks a little steeper than 35°. I can't measure that by eye, so check it. |
| 2 | World fit | 8 | A white-yellow core with a hard white highlight at the head's upper left, and a hot orange body. This fits "The light" (hard white highlights, glossy and wet) and "Stars die and are dragged in, still burning". It matches `look_reference` (orange-yellow comet, fading trail). The braid direction is followed. The head and its soft halo read as a burning star, not as a flat disc. |
| 3 | Colors | 8 | Head and trail stay in orange and yellow, the heat color in the color language. They are vivid and clean. There is no solid fuchsia, so rule 6 holds. The ribbons turn dull red-brown where they cross, and the far tip fades into a muddy dark orange. This lowers the "vivid" feel of the trail compared with the head. |
| 4 | Light & glow | 8 | Hazards glow hot (GDD 12 `glow`), and the head has a wide soft glow that is pre-rendered. A thin fuchsia rim sits on the head's bottom side, as rule 8 asks, and it is only a thin accent. The trail has no rim and little glow of its own. The GDD doesn't ask for more, but a little warm glow on the ribbons would tie them to the head. |
| 5 | Readability & finish | 7 | The head reads clearly at 1× on the dark background and on the painting. The braid is the weak part. At 1× the two ribbons are only about 2 to 3 px wide, and they read as one thin twisted strand, not as two ribbons. On the 4× board the crossings look blocky and stair-stepped along the upper-left. The trail is much dimmer than the head, so the "braided" direction is easy to miss at game size (Pillar 2, readable at a glance). The small 42 px version loses the twist almost fully. |

## Fix first
- Readability & finish: make each ribbon wider, or make the twist bigger, so two separate ribbons show at 1×. Keep the gap between them clear. Smooth the stair-stepped edges on the upper-left part of the trail.
- Colors: keep the crossings bright orange and yellow, not red-brown. Fade the far tip by brightness, not by turning it dull.
