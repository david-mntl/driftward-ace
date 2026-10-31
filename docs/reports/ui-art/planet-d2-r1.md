Score: 6.8 | Lowest: 6 | Size: 8

Asset: planet-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/planet-d2-r1.png
Board: staging/assets/sprites/planet-d2-r1-board.png
Measured: 64 × 64 px, 1 frame (still image)
GDD: 12-art-and-audio.md, drifters/08-planet.md, 07-drifters.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 64 × 64 matches `art_canvas`, and the body is a full circle that fills the radius 32 hitbox (`guess`). On the 4x board the hitbox ring shows as a thin teal line at the right and top-left edges, so the body may sit a hair inside the circle there. Check that the disc reaches the full radius on every side. No field rings are drawn in the image, as the spec asks. |
| 2 | World fit | 6 | The direction is "cracked rocky planet, as if islands are breaking off" (GDD 12 world brief: "Planets crack into floating islands"). The dark fissures are there. But the plates are even, rounded and tidy, so the body reads as a faceted ball or a stitched sphere, not a planet coming apart. Nothing is lifting off, shifting or leaving a gap between plates. The fissures are all the same thin width and never open into a wide rift. The mood is calm, not "beautiful and doomed". |
| 3 | Colors | 7 | A clean purple crust with lighter violet plates in the upper left and deep violet-navy shadows low right. This is the anomaly color (fuchsia and purple), and it is vivid and well separated. The whole body is darker and more blue-violet than the placeholder (140, 70, 200). The lower right goes close to the navy of space. The fissures are near-black, which fits "shadows go deep navy". The magenta rim at the bottom is bright and fairly wide, so it is more than a thin accent (rule 6). |
| 4 | Light & glow | 7 | The hard white highlight at top left fits "highlights are hard and white" (The light). The fuchsia rim runs along the bottom edge, on the side facing the black hole (rule 8). On the 4x board it is thick at the bottom center, a few px at 1×, and fades out toward the sides. Thin it, so it stays an accent and does not read as a solid fuchsia shape (rule 6). The highlight is a flat white blob. A smaller, harder spot with a soft falloff would look glossier. The planet has no glow, which fits: the field rings are drawn by the game. |
| 5 | Readability & finish | 6 | At 1× the disc reads as a purple planet with a bright spot, and the large plates at the top stay clear. The bottom third is the problem. It holds a cluster of tiny shards and fissures that blur into noise at 64 px. The dark lower-left fissures also sink into the navy background, so the silhouette loses its edge there. Edges look smooth in the master, but the fissures get blocky stair-steps at game size. A planet is a hazard (Pillar 2) and should read at a glance. |

## Fix first
- Readability & finish: cut the small shard cluster at the bottom. Use fewer, wider fissures that still show at 64 px. Keep a clear lighter edge on the lower left so the body doesn't sink into the navy.
- World fit: make the break-up show. Open one or two fissures wider, or let a plate sit raised or offset, so it reads as islands splitting off and not as a patterned ball. Keep the outer circle full so the hitbox still matches.
