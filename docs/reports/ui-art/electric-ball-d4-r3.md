Score: 8.0 | Lowest: 7 | Size: 9

Asset: electric-ball-d4
Kind: sprite
Round: 3
Image: staging/assets/sprites/electric-ball-d4-r3.png
Board: staging/assets/sprites/electric-ball-d4-r3-board.png
Measured: 24 × 24 px, 1 frame (still image, no animation frames)
GDD: 12-art-and-audio.md, drifters/10-electric-ball.md

Direction judged: design 4, "storm core: a swirling vortex of electricity". Only the 24 px image and the board were judged. The master PNG and the .piskel were not part of the rubric. The master is seen only as the board's 8× panel.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 24 × 24 matches `art_canvas` (`guess`). The vortex is centered. Its white core and dark indigo body sit inside the 16 px `ball_size` ring on the 4× board. The arms and the fuchsia arc reach toward the edge, as the spec allows. The ball has no hitbox, so nothing needs covering. |
| 2 | World fit | 8 | A hard white core with pale cyan arms and a soft halo fits "The light" (hard white highlights, vivid color) and the beautiful, lonely mood. It reads as a swirl of electricity, not a coin or a galaxy. In the master (8× panel) the arms now end in pale triangle spikes, which suits "spiky" in `look_reference`. At 24 px the spikes are only light blobs on the arms, so the shape is a round swirl. At 1× the white center with a dark ring can also read a little like an eye. |
| 3 | Colors | 8 | Core, arms and halo are pale white-cyan, which is the color language for electricity. The arms stay light cyan, apart from the ship's cobalt. The dark body is indigo, so it carries the purple. The one fuchsia arc is thin and sits at the bottom, so it follows rule 6 and does not read as a coin. The spec asks for "thin purple and fuchsia arcs". The purple arcs are only the indigo body and the faint halo fringe. A thin violet arc would match the wording better. |
| 4 | Light & glow | 8 | Hazards get glow (GDD 12 `glow`), and the pale cyan halo around a hard white core says electric. The round 2 problem is fixed. The only fuchsia arc is now on the bottom side, the side facing the black hole (rule 8), and it is thin in the master. At 4× and 8× it is slightly heavy, a 2 px band, so it is close to more than a "thin accent". The outer halo is still a soft purple-grey fringe that dulls the edge a little. |
| 5 | Readability & finish | 7 | At 1× on the dim purple haze (board, bottom) it is a clear bright swirl with a white center, easy to find. The arms are wider and fewer than in round 2, and the 4× view shows them as connected shapes. In the 8× zoom the lower arms and the spikes still break into stepped 1 px light and dark pixels, and the dark body and arms blur together. That is not yet the smooth, glossy edge `art_style` asks for. The sprite is clean at 1× but not crisp. |

## Fix first
- Readability & finish: keep the dark gaps between arms and body wider (at least 2 px) so the lower arms and spikes stay separate after the shrink. Give the spike tips a brighter value than the arms so they show at 24 px.
- Colors / Light & glow: thin the bottom fuchsia arc toward 1 px at game size. Add a thin violet arc, as `look_reference` asks, on the dark body or the halo edge.

## Since round 2
- Size: 9 to 9, no change.
- World fit: 8 to 8, no change. The master's spikes are now clearer triangles, but they still do not survive the shrink.
- Colors: 8 to 8, no change. The fuchsia is still thin and only at the bottom, and violet arcs are still faint.
- Light & glow: 7 to 8. The top right fuchsia arc is gone, so the rim is only on the bottom side (rule 8).
- Readability & finish: 7 to 7, no change. Wider, fewer arms help at 1× and 4×, but the 8× zoom still shows stepped fragments.
