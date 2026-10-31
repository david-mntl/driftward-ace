Score: 6.0 | Lowest: 5 | Size: 8

Asset: satellite-drifter-a
Kind: sprite
Round: 1
Image: staging/assets/sprites/satellite-drifter-a-r1.png
Board: staging/assets/sprites/satellite-drifter-a-r1-board.png
Measured: 180 × 12 px, 5 frames of 36 × 12 px
GDD: 12-art-and-audio.md, drifters/02-satellite.md, 07-drifters.md

## Documentation differences (read first)
- The brief asks for wings that swing about 25° to each side, in a loop 1,2,3,4,5,4,3,2 (back and forth). Two GDD rules do not cover this. `12-art-and-audio.md` rule 13 says a turning object uses a full turn in steps of 45° or less "so the loop has no back-and-forth". `drifters/02-satellite.md` rule 8 says "the satellite never rotates, so its boxes stay upright" and its `size` is a 12 × 12 body with a 36 × 6 bar. A swinging panel is neither. I scored the art as made. Proposed change, pending Director approval: add to `drifters/02-satellite.md` a motion line that allows a panel swing and states the range (about ±25°) and loop, and in rule 13 say whether a swing of a part, not the whole sprite, may go back and forth. Also say whether the 36 × 6 panel bar hitbox stays flat while the drawn panels tilt (rule 9 of 12-art says hitboxes never rotate).
- `drifters/02-satellite.md` `look_reference` says "white body with blue solar panels". The brief adds "destroyed" and "fuchsia magnetism rays". The spec has no such look yet. I judged against the brief and the color language.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 36 × 12 per frame matches the spec size (`guess`), and the 12 × 12 body fills the full frame height. At ±25° (frames 1 and 5) the panel tips reach the top and bottom frame edges on the board, so they may be clipped. The tilted panels also leave the flat 36 × 6 bar hitbox, so what the player sees no longer matches the hitbox in those frames. |
| 2 | World fit | 6 | The glossy light body and streaked panels fit "The light" and "Metal ships and satellites drift dead, or worse, half alive". The "looks destroyed" part does not show at 1×: the panels look whole and shiny, with no snapped edge, hole or missing piece. |
| 3 | Colors | 5 | The panels are washed with magenta and pink along most of their length (board, frames 1 to 5). Rule 6 says a solid bright fuchsia shape means a coin, and hazards may carry fuchsia only as thin accents. `look_reference` asks for blue panels, but they read purple-pink. The white body is clean. |
| 4 | Light & glow | 5 | The brief asks for glowing rays on the body, and a fuchsia rim goes on the bottom side (rule 8). At 1× the rays are not distinct: they read as a pink haze at the panel tips, not as separate rays. The rim is not clearly on the bottom edge of the body and panels. The light stays fixed across frames, as rule 13 wants. |
| 5 | Readability & finish | 6 | On the navy field the sprite reads as a small winged shape and the swing shows, since 25° is above the 20° floor in rule 13. But the dark core of the body sinks into the navy, so the silhouette looks like a saucer more than a satellite with a clear panel bar. Edges are smooth in the 2× view. The loop (5 frames played 1,2,3,4,5,4,3,2) is smooth. |

## Fix first
- Colors: pull the fuchsia off the panels. Keep them blue as `look_reference` says. Use fuchsia only as thin rim and ray accents (rule 6).
- Light & glow: draw the rays as separate, thin lines, and put the fuchsia rim on the bottom edge of the body and panels (rule 8). Keep the light fixed in all 5 frames.
- Also check frames 1 and 5 for clipping at the frame top and bottom edges.
