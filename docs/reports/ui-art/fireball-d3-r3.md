Score: 8.0 | Lowest: 8 | Size: 8

Asset: fireball-d3
Kind: sprite
Round: 3
Image: staging/assets/sprites/fireball-d3-r3.png
Board: staging/assets/sprites/fireball-d3-r3-board.png
Measured: 64 × 64 px, 1 frame (no animation frames, as asked)
GDD: 12-art-and-audio.md, drifters/06-fireball.md
Direction: design 3, plasma teardrop (smooth glossy teardrop, very hot white core, shorter trail)
Previous report: docs/reports/ui-art/fireball-d3-r2.md

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 64 × 64 matches `art_canvas` (`guess`). On the 4x board the head fills the head circle (r16), centered on the (44, 44) spot, and the path runs along the 35° diagonal toward the top-left. The trail is now clearly wider where it passes the tail circle (r8): the bright body fills most of that circle. A thin sliver of the circle's upper-left edge still sits on the dim edge of the trail, close to empty navy. Hazard rule 8 (a hitbox is never bigger than what the player sees) is nearly met, not fully. |
| 2 | World fit | 8 | A glossy teardrop with a hard white highlight and a white-hot core reads as a "star dragged in, still burning" (GDD 12 world brief, "What it does"). It matches `look_reference` (orange-yellow comet with a fading trail), and the short trail follows the design 3 direction. The soft haze on the head's right side is a little fuzzy for "glossy and wet" ("The light"), but it is mild. |
| 3 | Colors | 8 | White-yellow core, orange body, red-orange edge: heat colors only, as the color language asks for the fireball ("Orange and yellow: heat, danger"). Vivid and clean, no muddy browns, smooth steps along the trail. Fuchsia is a thin accent at the bottom of the head only, so it does not read as a coin (rule 6). |
| 4 | Light & glow | 8 | The thin fuchsia rim runs along the lower edge of the head, the side facing the black hole (rule 8). The hard white highlight and its short dashes sit at the right of the head ("Highlights are hard and white"). The hot orange glow suits a hazard (`glow`: hazards glow). At 1× the rim is very thin and mostly lost against the red-orange edge. It is correct as an accent, but it could be a touch more defined along the lower left. |
| 5 | Readability & finish | 8 | The shape and its direction of travel read at once at 1× on both the dark and the painting boards, and it is the brightest warm thing in the frame (Pillar 2, rule 2). The neck of the trail is brighter than in r2 and holds against the navy. Small flaw: the last few pixels of the trail's tip are still stepped, which shows on the 4x board. The small 42 version keeps the shape clean. |

## Fix first
- Size (tail coverage): push the bright body a little further out on the upper-left side of the tail circle (r8, centered about 16 px up-left of the head's center along the path), so the whole circle sits on visible trail. Keep the head where it is.
- Light & glow (rim): make the fuchsia rim slightly more defined along the lower left of the head so it still shows at 1×. Keep it thin (rule 6).

## Since round 2
- Size 7 → 8: the trail is wider at the tail circle and now covers most of it. A small sliver at the upper-left edge remains.
- Readability & finish 8 → 8: the neck is brighter, but the stepped tip is still there.
- World fit, Colors, Light & glow: unchanged at 8.
