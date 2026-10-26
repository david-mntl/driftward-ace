Score: 5.2 | Lowest: 3 | Size: 8

Asset: demo-ship
Kind: sprite
Round: 1
Image: staging/assets/sprites/demo-ship-r1.png
Board: staging/assets/sprites/demo-ship-r1-board.png
Measured: 32 × 32 px, 1 frame (32 × 32 px)
GDD: 12-art-and-audio.md, 04-ship.md, 07-drifters.md (rule 8)

The ship's `look` is TBD (SH-06). This round is scored against `look_reference` and the color language row for the ship, both `guess`.

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 32 × 32 matches `ship_w` × `ship_h` (guess). The foot of the inverted-T `hitbox` (guess), the bottom 12 rows, is filled almost edge to edge by the wings. The 12 px bar is filled down its length by the fuselage. The nose narrows to about 5 px at the top, so for the top 3 to 4 rows the bar's corners (about x 10–12 and 19–21) are empty black. There the hitbox is bigger than what the player sees (04-ship.md rule 8, 07-drifters.md rule 8). |
| 2 | World fit | 5 | Pale silver-grey plating with cobalt lines and a hard white highlight on the nose fit "You" and "The light" in the world brief. The thin fuchsia line along the bottom edge marks the ship as touched, but the brief says it "came through untouched: no shimmer". The wings read as a broad delta arrowhead, not the "long blade-like wings" of `look_reference`. Shadows under the wings are mid grey, not deep navy ("The light"). |
| 3 | Colors | 3 | The engine flame at bottom center (about x 14–18, y 26–30) is orange to yellow. In the color language that means heat and danger, and the ship's row asks for "a blue flame". The full-width fuchsia line on the bottom row (y 31) is the anomaly's color. `look_reference` says "No fuchsia". It is also a solid bright fuchsia shape, which rule 6 gives to coins. The cobalt lines and pale plating are right: clean and well separated. |
| 4 | Light & glow | 3 | The bottom-edge fuchsia rim breaks rule 8: "The ship has none: it is untouched." The orange flame glows like a hazard, which puts the ship in the heat color family. The hard white highlight on the nose follows "The light". How much the ship itself glows is TBD (SH-06), so that part is not scored. |
| 5 | Readability & finish | 7 | At 1× on the board the ship reads at a glance as a small pointed craft: pale body, cobalt outline, against the black `placeholder_bg` (guess). Edges are clean, with soft plating gradients in the 4× crop. The bright fuchsia bottom line reads as a separate bar cut off from the hull and pulls the eye away from the shape. Beside the planned fuchsia bottom glow (Background), it would blend into the edge where falling costs a life. |

## Fix first
- Colors: repaint the engine flame blue, as the ship's color language row and `look_reference` ask. No orange or yellow on the ship.
- Light & glow: remove the fuchsia rim from the bottom edge. The ship gets no rim (rule 8) and no fuchsia at all (`look_reference`).
