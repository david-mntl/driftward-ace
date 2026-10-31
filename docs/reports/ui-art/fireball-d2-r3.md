Score: 8.0 | Lowest: 7 | Size: 9

Asset: fireball-d2
Kind: sprite
Round: 3
Image: staging/assets/sprites/fireball-d2-r3.png
Board: staging/assets/sprites/fireball-d2-r3-board.png
Measured: 64 × 64 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md
Direction judged: design 2, burning rock (dark rock head wrapped in flame, ember sparks in the trail)
Previous report: docs/reports/ui-art/fireball-d2-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` (`guess`). On the board's hitbox overlay the head circle (r16) is filled by the rock and its flame ring, so the head hitbox is covered. The tail circle (r8) sits on the flame behind the head, but its upper-left edge falls on thin flame and the first loose sparks, so cover there is partial. The head sits low right and the trail runs up and left inside the canvas, as the spec says. I judged the head position from the overlay, not from measured pixels. |
| 2 | World fit | 8 | A cracked rock in a hot flame shell fits "Stars die and are dragged in, still burning" (world brief) and `look_reference` (orange-yellow comet, fading trail). Mood is beautiful and doomed, not horror. The blue-violet rock with orange cracks has the glossy, wet feel of "The light". The lower half of the rock is still fairly matte. |
| 3 | Colors | 8 | The round 2 problem is fixed. The ember sparks in the trail, at the top left of the head, are now orange and yellow like the flame, so no green cast is left. The flame runs orange to yellow ("heat, danger" in the color language). The rock's navy-violet shadows and orange cracks are clean ("shadows go deep navy"). The fuchsia stays a thin accent, so rule 6 is respected. The flame's inner yellow-white core is the only area that goes a bit flat. |
| 4 | Light & glow | 8 | A small hard white highlight sits on the rock's upper left, away from the black hole ("highlights are hard and white"). The flame is the glow: bright at the head and fading along the trail, so "hazards glow hot" is met. The rim light (rule 8) is a thin fuchsia and pink line on the head's bottom edge, on the side facing the black hole. A short pink fringe still shows at the bottom of the flame ring, a little past the head, but it is smaller than in round 2. There is no soft halo around the head. |
| 5 | Readability & finish | 7 | At 1× the bright flame ring separates the head from both the dark and the painting, and the diagonal shape reads as a comet diving down-right (Pillar 2). The rock's cracks stay visible. The 42 px small version stays readable. On the 4× view the flame and trail edges are still stepped, and the three loose ember sparks at the top left are still hard single squares. That is against "smooth and glossy" (`art_style`). Round 2's note on both points still stands. |

## Fix first
- Readability & finish: round the three ember sparks into soft dots, and smooth the stepped edge of the flame and trail on its upper-left side.
- Light & glow (next lowest of the 8s): pull the pink rim fringe back so it ends where the head's flame ring ends.

## Since round 2
- Colors 7 → 8: the ember sparks are now warm orange and yellow, not olive green.
- Light & glow 8 → 8: the rim is slightly shorter, but a pink fringe still shows at the bottom of the ring.
- Readability & finish 7 → 7: the sparks are still hard squares and the trail edge is still stepped.
- Size 9 and World fit 8: no change.
