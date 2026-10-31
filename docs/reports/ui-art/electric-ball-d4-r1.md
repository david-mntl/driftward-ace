Score: 7.0 | Lowest: 6 | Size: 9

Asset: electric-ball-d4
Kind: sprite
Round: 1
Image: staging/assets/sprites/electric-ball-d4-r1.png
Board: staging/assets/sprites/electric-ball-d4-r1-board.png
Measured: 24 × 24 px, 1 frame (still image, no animation frames)
GDD: 12-art-and-audio.md, drifters/10-electric-ball.md

Direction judged: design 4, "storm core: a swirling vortex of electricity". Only the 24 px image and the board were judged. The master PNG and the .piskel were not part of the rubric.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 24 × 24 matches `art_canvas` (`guess`). The ball is centered and the dark disc fills about the 16 px `ball_size` (`guess`). The spiral arms reach toward the edge, as the spec allows. The ball has no hitbox, so there is nothing to cover. The 4× board ring shows the arms staying inside the canvas. |
| 2 | World fit | 7 | A glowing, glossy vortex with a hot white core suits "The light" and the lonely, doomed mood. The spiral reads as a small galaxy or black hole more than as electricity. The coin is "a galaxy turning inside" a fuchsia and purple crystal (world brief, "The new universe"). A purple spiral disc is close to that look, and it risks a coin/hazard mix-up (Pillar 2). `look_reference` asks for "a spiky glowing orb". The smooth round body has no spikes. The arms are the only jagged part. |
| 3 | Colors | 6 | The color language says electricity is "pale white-cyan" and "kept away from the ship's blue". The core and arms are white with a lavender tint, and I see almost no cyan anywhere. The body is a large flat disc of dark indigo-purple. That is a big area of purple against thin white arcs, so it reads as magnetism, not electricity. The fuchsia is thin: one arc at lower right and a few pixels. That is correct under rule 6 and does not look like a coin. The deep purple body does not clash with the ship's cobalt. |
| 4 | Light & glow | 7 | Hazards get glow (GDD 12 `glow`), and this one has a soft purple halo and a hard white core highlight. Rule 8 puts the fuchsia rim on the bottom side. The fuchsia arc sits at the lower right and bottom of the ball, which follows it. The halo is violet, not white-cyan, so the glow does not say "electric" either. At 24 px the halo is only 1 or 2 px wide and mostly blends into the body. |
| 5 | Readability & finish | 6 | At 1× on the dim purple haze (board, bottom) it shows as a small violet swirl with a bright center. It is findable, but it is not obviously a hazard. The dark body is close to the haze color, so the outline depends on the halo. The arms are semi-transparent, so on the 8× zoom the edges look soft and stepped, with grey-lavender mid-tones. Rule 2 and art_style ask for clean, glossy shapes. The thin arms break into 1 px fragments at 1×. Also, the master's strong purple outer glow is lost after the shrink. |

## Fix first
- Colors: bring in the pale white-cyan the color language names for electricity. Make the core and the arc highlights white-cyan, not lavender. Shrink the dark purple body so it stops being the main color, and keep fuchsia as thin accents on the lower side.
- Readability & finish: make the arms brighter and more opaque so they survive the shrink as clean, jagged shapes. This also helps `look_reference` ("spiky"), separates the ball from the coin's galaxy look, and gives the ball a clear edge on the dim haze.
