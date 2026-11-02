Score: 7.2 | Lowest: 6 | Size: 9

Asset: meteorite-d3
Kind: sprite
Round: 1
Image: staging/assets/sprites/meteorite-d3-r1.png
Board: staging/assets/sprites/meteorite-d3-r1-board.png
Measured: 28 × 28 px, 1 frame (still image, no sheet)
GDD: 12-art-and-audio.md, drifters/01-meteorite.md, 07-drifters.md (not needed beyond shared rules)

Direction for this design: frost-crusted (dark rock, pale white-grey frost on the top half, no cyan, no blue).

| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Size | 9 | 28 × 28 matches the medium variant and `art_canvas` (`guess`). On the board's 4× view the round body reaches the edges of the r14 hitbox circle on all sides, as the spec asks ("the rock filling the hitbox circle"). One still frame, as the brief says. Not 10 because the lower-right edge sits a little inside the circle in the 4× view. |
| 2 | World fit | 7 | A plain rock with no tail and no glow, as `look_reference` asks. The frost cap follows the brief's direction and keeps cyan and ship-blue away. Glossy hard-white patches fit "The light". The frost makes the rock look like a snowball or a planet more than a broken rock, and the dark patches inside the frost can read as a face. The "mood" (beautiful and doomed) is mild. |
| 3 | Colors | 7 | Frost is white-grey with no cyan or blue, as the direction says. No solid fuchsia, so rule 6 holds. The dark rock body reads as warm brown-grey; the GDD says deep navy shadows, so push the lower half cooler and deeper. Orange and yellow mean heat, so keep the brown from drifting that way. |
| 4 | Light & glow | 7 | No glow, as `look_reference` demands. A thin fuchsia rim runs along the bottom edge, the side facing the black hole (rule 8), and it stays a thin accent. The rim is dim and broken at 1×, so it nearly vanishes on navy. The frost carries hard white highlights at top, which matches "hard and white". |
| 5 | Readability & finish | 6 | At 1× on navy and on the painting, the white cap reads at once, so the rock stands out. The dark lower half sinks into the navy, and the shape looks like a half-moon or a yin-yang more than a full circle (Pillar 2: the whole hazard should be readable). Frost edges are hard and blocky in the 4× view, not smooth like a glossy master shrunk down. The frost/rock boundary is noisy with a few isolated dark pixels inside the white. |

## Fix first
- Readability & finish: lift the dark lower half so its edge separates from the navy (a slightly lighter mid-tone rim of rock on the lower and left edges), so the full circle reads at 1×. Clean the frost edge into a few larger, smoother patches, and drop the isolated dark specks inside the white.
- Colors / Light & glow: cool and deepen the rock shadow toward deep navy-grey, and make the fuchsia bottom rim a little more continuous (still thin) so it shows at 1×.
