Score: 7.8 | Lowest: 7 | Size: 9

Asset: fireball-d2
Kind: sprite
Round: 2
Image: staging/assets/sprites/fireball-d2-r2.png
Board: staging/assets/sprites/fireball-d2-r2-board.png
Measured: 64 × 64 px, 1 frame (still)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md
Direction judged: design 2, burning rock (dark rock head wrapped in flame, ember sparks in the trail)
Previous report: docs/reports/ui-art/fireball-d2-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 64 × 64 matches `art_canvas` (`guess`). On the board's hitbox overlay the head circle (r16) is filled by the rock and its flame ring, so the head hitbox is covered. The tail circle (r8) sits on the flame and ember cloud behind the head and is covered. The head sits low right and the trail runs up and left inside the canvas, as the spec says. I judged the head position from the overlay, not from measured pixels. The far tip of the trail at the top left is still thin and faint. |
| 2 | World fit | 8 | A cracked rock inside a hot flame shell fits "Stars die and are dragged in, still burning" (world brief) and `look_reference` (orange-yellow comet, fading trail). Mood is beautiful and doomed, not horror. The rock now has a cooler blue-violet tone and a bright highlight, so it feels more like the glossy, wet look of "The light". The rock is still fairly matte across its lower half. |
| 3 | Colors | 7 | The flame runs orange to yellow, which matches "heat, danger" in the color language. The rock's navy-violet shadows with orange cracks are cleaner than round 1 and fit "shadows go deep navy". The ember sparks in the trail, at the upper left of the head (around the tail hitbox on the board), are a pale olive yellow-green. They read slightly green and muddy next to the clean orange flame. Heat colors should stay orange and yellow. The fuchsia stays a thin accent, so rule 6 is not claimed. |
| 4 | Light & glow | 8 | A small hard white highlight sits on the rock's upper left, away from the black hole, as "highlights are hard and white" asks. The flame is the glow: bright at the head and fading along the trail, so "hazards glow hot" is met. The rim light (rule 8) is a thin fuchsia and pink line on the head's bottom-left edge, on the side facing the black hole. It still runs a little past the head at the lower left, where a short pink dash sticks out of the flame ring. There is no soft halo around the head. |
| 5 | Readability & finish | 7 | At 1× the bright flame ring separates the head from both the dark and the painting, and the diagonal shape reads as a comet diving down-right (Pillar 2). The rock's cracks are now visible, so it no longer reads as a flat dark blob. The ember sparks are still hard single squares, which look blocky at 4×. The trail edge is stepped rather than smooth, against the "smooth and glossy" style (`art_style`). The 42 px small version stays readable. |

## Fix first
- Colors: shift the ember sparks from olive yellow-green to warm orange and yellow, so they match the flame.
- Readability & finish: soften the ember sparks into small rounded dots and smooth the stepped trail edge. Pull the pink rim back so it stops where the head's ring ends.

## Since round 1
- Colors 8 → 7: the rock is cleaner, but the ember sparks now read olive green and muddy beside the orange flame.
- Light & glow 7 → 8: the hard white highlight is on the rock's upper left, and the rim is thinner. A short pink tail still runs past the head.
- Readability & finish 7 → 7: the rock cracks read better, but the sparks and the trail edge are still blocky.
- Size 9 and World fit 8: no change.
