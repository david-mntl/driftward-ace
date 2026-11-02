Score: 6.0 | Lowest: 5 | Size: 7

Asset: electric-ball-d5
Kind: sprite
Round: 1
Image: staging/assets/sprites/electric-ball-d5-r1.png
Board: staging/assets/sprites/electric-ball-d5-r1-board.png
Measured: 24 × 24 px, no frames
GDD: 12-art-and-audio.md, drifters/10-electric-ball.md, 07-drifters.md (not needed beyond the spec; shared hazard rules only)

Direction for this design: fractal, branching arcs from the core, like a Lichtenberg figure.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 7 | The canvas is 24 × 24, as `art_canvas` asks (`guess`). The ball sits centered and the arcs run toward the edge. I can't measure the ball's width, so I can't confirm the 16 px `ball_size` (`guess`). By eye on the board, the violet body looks like it fills most of the 24 px box, more than a 16 px ball with arcs around it would. Please give the measured body width next round. |
| 2 | World fit | 6 | A glowing orb with a bright white core and fuchsia lower arcs fits "Hazards glow hot" and the mood in GDD 12. The look is a soft violet sphere with little spikes, which reads as a plasma globe or a sea urchin. It does not follow this design's direction: there are no long branching arcs from the core, only short stubs, the longest hanging below. `look_reference` asks for a "spiky glowing orb" with thin arcs, so it is close, but the Lichtenberg branching is missing. |
| 3 | Colors | 5 | Color language says electricity is a pale white-cyan core with thin purple and fuchsia arcs. Here the white core is small and has no cyan tint that I can see. A large lavender-violet disc takes most of the area, so the body reads as a purple ball, not a white-cyan core. The darker violet shading in the lower body is mid-tone and slightly muddy against the navy. Fuchsia is kept to thin accents on the lower arcs (rule 6 is respected). It stays away from the ship's cobalt. |
| 4 | Light & glow | 6 | A hazard may glow (GDD 12 `glow`), and the white center with a soft violet falloff does that. Rule 8 is followed: the fuchsia rim and arcs sit on the bottom side, facing the black hole. The upper arcs are pale violet and no fuchsia, which is right. The glow is thick and chunky and swallows the thin arcs instead of leaving a bright core with sharp arcs around it. |
| 5 | Readability & finish | 6 | At 1× on the dark board it reads clearly as a bright round object, and it is easy to see on navy (rule 2). The arcs are the weak part. The stubs on the upper and lower sides are blocky, with visible stair-steps, and they look like pixel blobs, not thin smooth lines. `art_style` asks for smooth, glossy and not pixel art. The shape is also mostly a disc, so the "thin arcs" idea does not read at game size. |

## Fix first
- Colors: shrink the violet disc, make the core pale white-cyan and bright, and let the purple and fuchsia live in thin arcs, not in the body.
- Readability & finish: redraw the arcs as thin, smooth, branching lines (forks that split from the core and reach toward the edge), so the fractal direction reads. Check the ball body is 16 px wide and report the measured number.
