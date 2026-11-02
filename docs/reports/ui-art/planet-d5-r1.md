Score: 7.4 | Lowest: 7 | Size: 9

Asset: planet-d5
Kind: sprite
Round: 1
Image: staging/assets/sprites/planet-d5-r1.png
Board: staging/assets/sprites/planet-d5-r1-board.png
Measured: 64 × 64 px, 1 frame (no animation frames, as briefed)
GDD: 12-art-and-audio.md, drifters/08-planet.md
Direction for this design: ocean world, deep violet seas and pale continents.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` and `size` (`guess`). On the 4× board the sphere reaches all four sides of the hitbox circle (r32), with no field rings in the image, as `art_canvas` asks. I judged the fill by eye on the board only. The measured numbers confirm the canvas, not the circle's exact edge. |
| 2 | World fit | 7 | A glossy sphere with a hard white spot at the top left and a fuchsia rim fits "The light" and "touched by the anomaly" in the world brief. The ocean direction is followed: dark violet seas, pale lavender land. The pale patches are blotchy and soft-edged. They read as cloud or ice more than as continents. There are no coastline shapes. |
| 3 | Colors | 7 | Clean violet and lavender, not muddy. The seas are a deep indigo-violet, bluer than the placeholder purple (140, 70, 200), which is a `guess`. The palette stays away from the ship's cobalt and from orange and yellow. The fuchsia is a thin accent only (rule 6). The pale land and the white spot are close in value. The sphere has few mid-tones. |
| 4 | Light & glow | 7 | The fuchsia rim runs along the bottom edge, the side facing the black hole (rule 8), and is thin. The highlight is a small hard white spot at the top left (world brief "hard and white"). The shadow side at the bottom right is deep violet, not near-black navy as the brief says. The terminator is soft, so the sphere looks only slightly round. No outer glow is drawn. The spec asks for none, only for a rim. |
| 5 | Readability & finish | 7 | At 1× it reads at once as a round purple body on the dark navy background. The bright left and top edges separate well. The dark bottom-right sea sits close to the navy background and leans on the rim to hold its edge. The edge is smooth, with no jaggies. Land and sea detail is soft and slightly blurry at 1×, so the "ocean" idea is hard to see at game size. |

## Fix first
- World fit: give the pale land harder, more defined coastlines so it reads as continents at 1×, not as clouds.
- Colors: widen the value range. Make the seas a little more purple than indigo, and add a clear mid-tone between sea and land. Then the sphere reads rounder and the terminator shows.
