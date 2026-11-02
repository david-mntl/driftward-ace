Score: 7.8 | Lowest: 7 | Size: 7

Asset: fireball-d3
Kind: sprite
Round: 2
Image: staging/assets/sprites/fireball-d3-r2.png
Board: staging/assets/sprites/fireball-d3-r2-board.png
Measured: 64 × 64 px, 1 frame (no animation frames, as asked)
GDD: 12-art-and-audio.md, drifters/06-fireball.md, 07-drifters.md
Direction: design 3, plasma teardrop (smooth glossy teardrop, very hot white core, shorter trail)
Previous report: docs/reports/ui-art/fireball-d3-r1.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 7 | 64 × 64 matches `art_canvas` (`guess`). On the 4x board the head fills the head circle (r16) with its center on the (44, 44) spot, and the path runs at the 35° diagonal toward the top-left. The tail circle (r8) is still not covered well. The trail passes through the circle's center but is only about half the circle's width there, so the upper-right and lower-left sides of the tail circle sit on empty navy. Hazard rule 8 says a hitbox is never bigger than what the player sees. The spec allows the trail to run past the tail circle, not to be narrower than it. |
| 2 | World fit | 8 | A glossy teardrop with a hard white highlight and a white-hot core reads as a "star dragged in, still burning" (GDD 12 world brief, "What it does"). It matches `look_reference` (orange-yellow comet with a fading trail), and the short trail follows the design 3 direction. The soft outer haze on the head's right side is a little fuzzy for "glossy and wet" ("The light"), but it is mild. |
| 3 | Colors | 8 | White-yellow core, orange body, red-orange edge: heat colors only, as the color language asks for the fireball ("Orange and yellow: heat, danger"). Vivid and clean, no muddy browns, and the steps along the trail are smooth. Fuchsia stays a thin accent at the bottom of the head, so it does not read as a coin (rule 6). |
| 4 | Light & glow | 8 | The thin fuchsia rim runs along the bottom of the head, on the side facing the black hole (rule 8). The hard white highlight and its small dashes sit at the upper right of the head ("Highlights are hard and white"). The hot glow suits a hazard (`glow`: hazards glow). At 1× the rim is very thin and mostly lost against the red-orange edge. It is correct as an accent, but it could be a touch more defined along the lower left. |
| 5 | Readability & finish | 8 | The round-1 stray squares are gone: the trail now ends in one connected, tapering tip, and the whole shape is smooth at 1×. The shape and direction of travel read at once on both the dark and the painting boards, and it is the brightest warm thing in the frame (Pillar 2, rule 2). Two small flaws remain. The trail's thin neck, between the tip and the head, is faint against the navy. The tip's last few pixels are stepped, which shows at 4x. |

## Fix first
- Size (tail coverage): widen the trail where it passes the tail circle (r8, centered about 16 px up-left of the head's center along the path), so the bright body spans most of that circle's width and not only its diagonal. Keep the head where it is.
- Readability & finish (neck): make the neck of the trail a little brighter so it holds against the navy at 1×, and round off the last stepped pixels of the tip.

## Since round 1
- Size 8 → 7: the trail root is wider than in r1, but the tail circle is still only half covered across its width. I scored the coverage more strictly this round.
- Readability & finish 7 → 8: the detached blocky specks are gone and the tip is connected and smooth.
- World fit, Colors, Light & glow: unchanged at 8.
