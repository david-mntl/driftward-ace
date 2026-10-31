Score: 7.6 | Lowest: 7 | Size: 9

Asset: electric-ball-d2
Kind: sprite
Round: 1
Image: staging/assets/sprites/electric-ball-d2-r1.png
Board: staging/assets/sprites/electric-ball-d2-r1-board.png
Measured: 24 × 24 px, no frames (still image)
GDD: 12-art-and-audio.md, drifters/10-electric-ball.md (07-drifters.md not needed: this round is a still, no entry warning)
Direction judged: design 2, urchin (sharp crackling spikes pointing outward)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 24 × 24 matches `art_canvas` (`guess`). On the 4x zoom the body sits inside the 16 px `ball_size` ring and the spikes and arcs stay inside the canvas, as the spec allows. The ball has no hitbox, so there is nothing else to cover. Small point: the spikes only reach a few px past the ball, so the "arcs may reach out to the edge" room is barely used. |
| 2 | World fit | 8 | A glossy orb with a hard white highlight at top left, a deep-navy-to-cyan body and a fuchsia lower edge fits "The light" (hard white highlights, glossy and wet) and the anomaly mark. It reads as a spiky glowing orb, which is the `look_reference`. The urchin direction is followed in the master, with pale shards pointing out all around. At game size the spikes are short and blunt, so the "sharp crackling" feel is mostly lost. |
| 3 | Colors | 7 | Core, spikes and arcs are pale white-cyan and purple, as the color language says for electricity, and nothing sits in cobalt. Two issues. The core's lower half is a fairly saturated sky-cyan, not the "pale white-cyan" the table names, and it comes closer to the ship's blue than it needs to. The fuchsia rim on the bottom is thick and bright (about a 2 px band at 1×), where rule 6 allows fuchsia only as a thin accent on a hazard. The purple arcs on the left and right are dark and sink into the navy at 1×. |
| 4 | Light & glow | 7 | The fuchsia rim is on the bottom side, facing the black hole (rule 8), and the top-left highlight is hard and white. Both are right. Glow is weak: the board's master shows almost no soft halo around the ball or the spikes, and GDD 12 `glow` asks for hazards to glow. The rim is also strong enough to compete with the core instead of being a thin edge. |
| 5 | Readability & finish | 7 | On the dim purple haze strip and on the navy board, the ball is clearly the brightest thing and shows at a glance at 1× (Pillar 2). Edges of the body are smooth. The spike ring turns into a fuzzy, speckled edge at 1× and 4×: the pale pixels and dark purple pixels alternate and do not read as separate spikes. The thin arcs are lost at game size. |

## Fix first
- Colors: lighten the core toward pale white-cyan (keep the saturated cyan only at the lower edge, if at all) and thin the fuchsia rim to about 1 px. Lift the purple arcs so they stay visible against navy.
- Readability & finish: make fewer, longer spikes so each one reads as a point at 1×, and add a soft pre-rendered halo (rule 3) so the spikes separate from the dark.
