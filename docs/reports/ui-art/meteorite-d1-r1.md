Score: 7.0 | Lowest: 6 | Size: 9

Asset: meteorite-d1
Kind: sprite
Round: 1
Image: staging/assets/sprites/meteorite-d1-r1.png
Board: staging/assets/sprites/meteorite-d1-r1-board.png
Measured: 28 × 28 px, no frames (one still)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md

Direction followed: dark basalt, blocky and angular, near-black with deep cracks, hard white highlights on the up-right edges.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (a still of the medium rock). On the board the rock fills the hitbox circle (radius 14, `guess`) and stays inside it, so the hitbox never exceeds what the player sees (07-drifters rule 8). The angular outline leaves small empty gaps at some corners of the circle, so coverage is not full everywhere. |
| 2 | World fit | 7 | A plain rock with no tail and no glow, as `look_reference` asks. The angular facets, dark cracks and hard white edge highlights at the top right fit "The light" (glossy, hard white highlights, deep shadows). The interior shows a blocky mosaic of cells at 4× on the board. That reads a little as pixel art, and `art_style` says smooth and glossy, not pixel art. |
| 3 | Colors | 6 | The body is near-black violet-navy with grey-violet facets. That follows the direction and does not use heat colors (orange/yellow), which is right for a plain rock. The darkest cells have almost no hue difference from the navy backdrop, so the body looks flat and slightly muddy. The fuchsia rim is the only saturated color and it is bright and solid along the bottom left; rule 6 allows fuchsia on hazards only as a thin accent. |
| 4 | Light & glow | 6 | Hard white highlights sit on the up-right edges, as the direction asks. A fuchsia rim runs along the bottom-left side, facing the black hole (rule 8). No glow, correct for the meteorite (`look_reference`). The rim is the weak part: at 4× on the board it looks about as thick as the highlights and runs a long arc, so it reads as more than a thin rim. The white highlights are also split into short dashes, so the light direction reads less clearly than one clean edge line. |
| 5 | Readability & finish | 6 | At 1× on the dim backdrop the silhouette reads because of the white highlights and the rim. Without them the near-black body sinks into the navy (Pillar 2, rule 2). The cracks inside are too dark and too small to read at 1×. They add noise, not shape. Edges of the outline are clean and the shape is a clear rounded polygon. |

## Fix first
- Colors: lift the facets slightly in value and hue, so the body separates from the navy background. Keep it dark but not near-black everywhere. Keep fuchsia thin.
- Readability & finish / Light & glow: thin the fuchsia rim to a narrower line, and merge the white highlights into one clean edge along the up-right side. Make fewer, bolder cracks so they show at 1×.
