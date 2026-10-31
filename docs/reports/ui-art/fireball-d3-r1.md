Score: 7.8 | Lowest: 7 | Size: 8

Asset: fireball-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/fireball-d3-r1.png
Board: staging/assets/sprites/fireball-d3-r1-board.png
Measured: 64 × 64 px, 1 frame (no animation frames, as asked)
GDD: 12-art-and-audio.md, drifters/06-fireball.md (07-drifters.md not needed for this still)
Direction: design 3, plasma teardrop (smooth glossy teardrop, very hot white core, shorter trail)

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 8 | 64 × 64 matches `art_canvas` (`guess`). On the 4x board the head fills the head circle (r16) at the lower right, so the head sits on the (44, 44) spot and flies at the 35° diagonal. The tail circle (r8) sits on the thick root of the trail, but the trail narrows quickly toward the top-left. The upper-left edge of the tail circle reaches past the visible body, so the tail hitbox is only partly covered. The spec allows the trail to run past the tail hitbox, not to stop short of it. |
| 2 | World fit | 8 | A glossy teardrop with a hard white highlight and a hot core reads as a "star dragged in, still burning" (GDD 12 world brief, "What it does"). It matches `look_reference` (orange-yellow comet with a fading trail). The shorter trail follows the design 3 direction. The very soft outer glow on the head's right side leans a little toward "fuzzy flame" rather than "glossy and wet". |
| 3 | Colors | 8 | White-yellow core, orange body and a red-orange edge: all heat colors, as the color language asks for the fireball ("Orange and yellow: heat, danger"). Vivid and clean, with no muddy browns. The fuchsia is only a thin arc, so it does not read as a coin (rule 6). The yellow-to-orange steps in the trail are smooth. |
| 4 | Light & glow | 8 | The thin fuchsia rim runs along the bottom of the head, on the side facing the black hole (rule 8). The hard white highlight sits at the upper right of the head, with small white dashes (rule: "Highlights are hard and white"). Hazards glow hot, and this one does. At 1× the fuchsia rim is very thin and barely shows against the red-orange edge. It stays an accent, which is correct, but it could be a touch cleaner along the lower right. |
| 5 | Readability & finish | 7 | The teardrop shape and the direction of travel read at once on the dark background and on the painting background. Pillar 2 is met: it is the brightest warm thing in the frame. The flaws are at the trail's far end. The last three specks are small, separate squares that look blocky next to the smooth head, and they look like stray pixels at 1×. The trail's thin neck is also faint against the navy, so the tail looks thinner than its hitbox. The head's outer glow is soft, so the exact edge of the head is hard to place. |

## Fix first
- Readability & finish: replace the blocky detached specks at the end of the trail with a smooth fade that stays connected to the trail. Make the neck of the trail a little brighter and wider so it holds against the navy at 1×.
- Size (tail coverage): widen the trail's root so it covers the tail hitbox circle (r8) all the way along its upper-left side. Keep the head where it is.
